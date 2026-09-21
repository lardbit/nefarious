from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from requests import Timeout
from rest_framework.test import APIClient

from nefarious import quality
from nefarious.jackett import get_filtered_jackett_indexers, get_jackett_search_url
from nefarious.models import NefariousSettings, QualityProfile
from nefarious.search import SEARCH_MEDIA_TYPE_MOVIE, SearchTorrents


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

    @patch('nefarious.search.requests.get')
    def test_non_integer_size_and_seeders_do_not_discard_results(self, requests_get):
        requests_get.return_value = self.response(b'''<rss xmlns:torznab="http://torznab.com/schemas/2015/feed">
          <channel>
            <item>
              <title>Float Size</title>
              <guid>float-size</guid>
              <size>123.45</size>
              <torznab:attr name="seeders" value="N/A" />
            </item>
            <item>
              <title>Valid Numbers</title>
              <guid>valid-numbers</guid>
              <size>456</size>
              <torznab:attr name="seeders" value="7" />
            </item>
          </channel>
        </rss>''')

        search = SearchTorrents(SEARCH_MEDIA_TYPE_MOVIE, 'Test Movie')

        self.assertTrue(search.ok)
        self.assertEqual(2, len(search.results))
        self.assertEqual(123, search.results[0]['Size'])
        self.assertEqual(0, search.results[0]['Seeders'])
        self.assertEqual(456, search.results[1]['Size'])
        self.assertEqual(7, search.results[1]['Seeders'])

    @patch('nefarious.search.requests.get')
    def test_results_without_guid_or_link_remain_distinct(self, requests_get):
        requests_get.return_value = self.response(b'''<rss>
          <channel>
            <item><title>First Result</title></item>
            <item><title>Second Result</title></item>
          </channel>
        </rss>''')

        search = SearchTorrents(SEARCH_MEDIA_TYPE_MOVIE, 'Test Movie')

        self.assertTrue(search.ok)
        self.assertEqual(2, len(search.results))
        self.assertNotEqual(search.results[0]['Guid'], search.results[1]['Guid'])

    @patch('nefarious.search.requests.get')
    def test_unsafe_xml_is_rejected_and_contained(self, requests_get):
        requests_get.return_value = self.response(b'''<!DOCTYPE rss [
          <!ENTITY unsafe "unsafe-value">
        ]>
        <rss><channel><item><title>&unsafe;</title></item></channel></rss>''')

        search = SearchTorrents(SEARCH_MEDIA_TYPE_MOVIE, 'Test Movie')

        self.assertFalse(search.ok)
        self.assertEqual([], search.results)
        self.assertIn('EntitiesForbidden', search.error_content)

    def test_timeout_model_validation(self):
        self.settings.jackett_search_timeout = 121
        with self.assertRaises(ValidationError):
            self.settings.full_clean()


class JackettSettingsApiTest(JackettTestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_timeout_persists_through_api(self):
        response = self.client.patch(
            '/api/settings/{}/'.format(self.settings.id),
            {'jackett_search_timeout': 75},
            format='json',
        )

        self.assertEqual(200, response.status_code)
        self.settings.refresh_from_db()
        self.assertEqual(75, self.settings.jackett_search_timeout)

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
