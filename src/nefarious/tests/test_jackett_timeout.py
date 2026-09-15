from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient
from requests import Timeout

from nefarious import quality
from nefarious.jackett import (
    get_filtered_jackett_indexers,
    get_jackett_indexers,
    get_jackett_search_url,
    get_jackett_session_cookie,
)
from nefarious.models import JackettIndexer, NefariousSettings, QualityProfile
from nefarious.search import SEARCH_MEDIA_TYPE_MOVIE, SearchTorrents
from nefarious.tasks import sync_jackett_indexers


TORZNAB_XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:torznab="http://torznab.com/schemas/2015/feed">
  <channel>
    <item>
      <title>Test Movie 2026 1080p WEB-DL</title>
      <guid>https://tracker.test/details/1</guid>
      <jackettindexer id="healthy">Healthy Tracker</jackettindexer>
      <size>123456</size>
      <link>http://jackett:9117/dl/healthy/1</link>
      <torznab:attr name="seeders" value="42" />
      <torznab:attr name="magneturl" value="magnet:?xt=urn:btih:abc" />
    </item>
  </channel>
</rss>'''


class JackettTestCase(TestCase):

    def setUp(self):
        quality_profile = QualityProfile.objects.create(name=quality.SDTV, quality=quality.SDTV)
        self.settings = NefariousSettings.objects.create(
            quality_profile_tv=quality_profile,
            quality_profile_movies=quality_profile,
        )

    @staticmethod
    def response(content=TORZNAB_XML):
        response = Mock(content=content, url='http://jackett.test/search')
        response.raise_for_status.return_value = None
        return response


class SearchTorrentsTest(JackettTestCase):

    @patch('nefarious.search.requests.get')
    def test_uses_torznab_endpoint_configured_filter_and_timeout(self, requests_get):
        self.settings.jackett_filter_index = '!status:failing+test:passed+!tag:nsfw'
        self.settings.jackett_search_timeout = 73
        self.settings.save()
        requests_get.return_value = self.response()

        search = SearchTorrents(SEARCH_MEDIA_TYPE_MOVIE, 'Test Movie')

        self.assertTrue(search.ok)
        self.assertEqual(1, len(search.results))
        self.assertEqual('Test Movie 2026 1080p WEB-DL', search.results[0]['Title'])
        self.assertEqual('Healthy Tracker', search.results[0]['Tracker'])
        self.assertEqual('healthy', search.results[0]['TrackerId'])
        self.assertEqual(42, search.results[0]['Seeders'])
        self.assertEqual('magnet:?xt=urn:btih:abc', search.results[0]['MagnetUri'])

        url = requests_get.call_args.args[0]
        kwargs = requests_get.call_args.kwargs
        self.assertEqual(
            'http://jackett:9117/api/v2.0/indexers/'
            '!status:failing+test:passed+!tag:nsfw/results/torznab',
            url,
        )
        self.assertEqual(73, kwargs['timeout'])
        self.assertEqual('search', kwargs['params']['t'])
        self.assertEqual('Test Movie', kwargs['params']['q'])
        self.assertNotIn('Query', kwargs['params'])
        self.assertNotIn('Category[]', kwargs['params'])

    @patch('nefarious.search.requests.get', side_effect=Timeout('slow indexer'))
    def test_timeout_is_retried_and_contained(self, requests_get):
        search = SearchTorrents(SEARCH_MEDIA_TYPE_MOVIE, 'Test Movie')

        self.assertFalse(search.ok)
        self.assertEqual([], search.results)
        self.assertIn('slow indexer', search.error_content)
        self.assertEqual(2, requests_get.call_count)

    @patch('nefarious.search.SearchTorrents._reset_indexer_failures')
    @patch('nefarious.search.SearchTorrents._record_indexer_failure')
    @patch('nefarious.search.SearchTorrents._get_indexer_failure_count', return_value=0)
    @patch('nefarious.search.SearchTorrents._request_results')
    @patch('nefarious.search.get_filtered_jackett_indexers')
    def test_isolated_search_contains_failure_and_serializes_flagged_indexer(
            self, get_indexers, request_results, get_failure_count,
            record_failure, reset_failures):
        self.settings.jackett_serialize_flaresolverr_indexers = True
        self.settings.save()
        JackettIndexer.objects.create(
            indexer_id='flaresolverr',
            name='FlareSolverr Tracker',
            is_flaresolverr=True,
        )
        get_indexers.return_value = [
            {'id': 'healthy', 'name': 'Healthy'},
            {'id': 'broken', 'name': 'Broken'},
            {'id': 'flaresolverr', 'name': 'FlareSolverr'},
        ]
        calls = []

        def result_for(indexer_id):
            calls.append(indexer_id)
            if indexer_id == 'broken':
                raise Timeout('broken timed out')
            return [{
                'Guid': indexer_id,
                'Title': indexer_id,
                'Link': '',
                'MagnetUri': None,
                'Size': 1,
                'Seeders': 1,
                'Tracker': indexer_id,
                'TrackerId': indexer_id,
            }]

        request_results.side_effect = result_for

        search = SearchTorrents(SEARCH_MEDIA_TYPE_MOVIE, 'Test Movie')

        self.assertTrue(search.ok)
        self.assertEqual({'healthy', 'flaresolverr'}, {result['Guid'] for result in search.results})
        self.assertEqual('flaresolverr', calls[-1])
        self.assertEqual(2, calls.count('broken'))
        record_failure.assert_called_once_with('broken')
        reset_failures.assert_any_call('healthy')
        reset_failures.assert_any_call('flaresolverr')

    def test_manual_override_wins_over_synced_tag(self):
        indexer = JackettIndexer.objects.create(
            indexer_id='example',
            name='Example',
            is_flaresolverr=True,
            is_flaresolverr_manual_override=False,
        )
        self.assertFalse(indexer.effective_is_flaresolverr)

        indexer.is_flaresolverr = False
        indexer.is_flaresolverr_manual_override = True
        self.assertTrue(indexer.effective_is_flaresolverr)

    def test_timeout_model_validation(self):
        self.settings.jackett_search_timeout = 121
        with self.assertRaises(ValidationError):
            self.settings.full_clean()


class JackettIndexerSyncTest(JackettTestCase):

    @patch('nefarious.tasks.get_jackett_indexers')
    def test_sync_populates_tags_without_replacing_manual_override(self, get_indexers):
        existing = JackettIndexer.objects.create(
            indexer_id='1337x',
            name='Old Name',
            is_flaresolverr=False,
            is_flaresolverr_manual_override=False,
        )
        get_indexers.return_value = [
            {'id': '1337x', 'name': '1337x', 'tags': ['public', 'FlareSolverr']},
            {'id': 'plain', 'name': 'Plain', 'tags': []},
        ]

        result = sync_jackett_indexers()

        self.assertEqual({'success': True, 'synced': 2}, result)
        existing.refresh_from_db()
        self.assertTrue(existing.is_flaresolverr)
        self.assertFalse(existing.is_flaresolverr_manual_override)
        self.assertIsNotNone(existing.last_synced_at)
        self.assertFalse(JackettIndexer.objects.get(indexer_id='plain').is_flaresolverr)

    @patch('nefarious.tasks.logger_background.warning')
    @patch('nefarious.tasks.get_jackett_indexers', side_effect=Timeout('login failed'))
    def test_sync_auth_failure_is_graceful_and_preserves_rows(self, get_indexers, warning):
        existing = JackettIndexer.objects.create(
            indexer_id='existing',
            name='Existing',
            is_flaresolverr=True,
            is_flaresolverr_manual_override=True,
        )

        result = sync_jackett_indexers()

        self.assertFalse(result['success'])
        existing.refresh_from_db()
        self.assertTrue(existing.is_flaresolverr)
        self.assertTrue(existing.is_flaresolverr_manual_override)
        warning.assert_called_once()


class JackettSettingsApiTest(JackettTestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_settings_and_manual_override_persist_through_api(self):
        indexer = JackettIndexer.objects.create(
            indexer_id='example',
            name='Example',
            is_flaresolverr=False,
        )

        response = self.client.patch(
            '/api/settings/{}/'.format(self.settings.id),
            {
                'jackett_search_timeout': 75,
                'jackett_serialize_flaresolverr_indexers': True,
            },
            format='json',
        )
        self.assertEqual(200, response.status_code)
        self.settings.refresh_from_db()
        self.assertEqual(75, self.settings.jackett_search_timeout)
        self.assertTrue(self.settings.jackett_serialize_flaresolverr_indexers)

        response = self.client.patch(
            '/api/jackett-indexers/{}/'.format(indexer.id),
            {
                'is_flaresolverr': True,
                'is_flaresolverr_manual_override': True,
            },
            format='json',
        )
        self.assertEqual(200, response.status_code)
        indexer.refresh_from_db()
        self.assertFalse(indexer.is_flaresolverr)
        self.assertTrue(indexer.is_flaresolverr_manual_override)
        self.assertTrue(response.data['effective_is_flaresolverr'])

    def test_timeout_outside_safe_range_is_rejected_by_api(self):
        response = self.client.patch(
            '/api/settings/{}/'.format(self.settings.id),
            {'jackett_search_timeout': 121},
            format='json',
        )
        self.assertEqual(400, response.status_code)


class JackettUrlTest(JackettTestCase):

    def test_filter_falls_back_to_all_only_when_unset(self):
        self.assertIn('/indexers/all/results/torznab', get_jackett_search_url(self.settings))
        self.settings.jackett_filter_index = 'tag:movies'
        self.assertIn('/indexers/tag:movies/results/torznab', get_jackett_search_url(self.settings))

    @patch('nefarious.jackett.requests.get')
    def test_filtered_indexer_lookup_uses_the_configured_filter(self, requests_get):
        self.settings.jackett_filter_index = '!status:failing+tag:movies'
        self.settings.jackett_search_timeout = 61
        self.settings.save()
        requests_get.return_value = self.response(
            b'<indexers><indexer id="movies"><title>Movies</title></indexer></indexers>'
        )

        indexers = get_filtered_jackett_indexers(self.settings)

        self.assertEqual([{'id': 'movies', 'name': 'Movies'}], indexers)
        self.assertIn(
            '/indexers/!status:failing+tag:movies/results/torznab',
            requests_get.call_args.args[0],
        )
        self.assertEqual(61, requests_get.call_args.kwargs['timeout'])
        self.assertEqual('indexers', requests_get.call_args.kwargs['params']['t'])

    @patch('nefarious.jackett.requests.Session')
    def test_session_login_without_password_follows_login_flow(self, session_class):
        session = session_class.return_value
        session.get.return_value = self.response()

        result = get_jackett_session_cookie(self.settings)

        self.assertIs(session, result)
        session.get.assert_called_once_with('http://jackett:9117/UI/Login', timeout=90)
        session.post.assert_not_called()

    @patch('nefarious.jackett.requests.Session')
    def test_password_login_posts_to_dashboard_and_fetches_tags(self, session_class):
        self.settings.jackett_admin_password = 'secret'
        self.settings.save()
        session = session_class.return_value
        login_response = self.response()
        indexer_response = self.response()
        indexer_response.json.return_value = [
            {'id': 'example', 'name': 'Example', 'tags': ['flaresolverr']},
        ]
        session.get.side_effect = [login_response, indexer_response]
        session.post.return_value = login_response

        indexers = get_jackett_indexers(self.settings)

        self.assertEqual('example', indexers[0]['id'])
        session.post.assert_called_once_with(
            'http://jackett:9117/UI/Dashboard',
            data={'password': 'secret'},
            timeout=90,
        )
        self.assertEqual(
            {'configured': 'true'},
            session.get.call_args_list[1].kwargs['params'],
        )
