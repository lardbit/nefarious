from unittest.mock import Mock, patch

from django.test import TestCase

from nefarious.processors import WatchProcessorBase
from nefarious.utils import count_live_seeders


class CountLiveSeedersTest(TestCase):
    def test_counts_full_seeds(self):
        client = Mock()
        client.get_torrent.return_value = Mock(fields={'peers': [
            {'progress': 1.0},
            {'progress': 0.5},
            {'progress': 1.0},
        ]})
        self.assertEqual(count_live_seeders(client, 99), 2)

    def test_partial_peers_are_not_seeds(self):
        client = Mock()
        client.get_torrent.return_value = Mock(fields={'peers': [{'progress': 0.5}]})
        self.assertEqual(count_live_seeders(client, 99), 0)

    def test_no_peers_key(self):
        client = Mock()
        client.get_torrent.return_value = Mock(fields={})
        self.assertEqual(count_live_seeders(client, 99), 0)

    def test_peers_none(self):
        client = Mock()
        client.get_torrent.return_value = Mock(fields={'peers': None})
        self.assertEqual(count_live_seeders(client, 99), 0)


class TorrentHasSeedersTest(TestCase):
    @patch('nefarious.processors.count_live_seeders')
    @patch('nefarious.processors.time.sleep')
    def test_has_seeders_returns_true_immediately(self, mock_sleep, mock_count):
        processor = WatchProcessorBase.__new__(WatchProcessorBase)
        processor.transmission_client = Mock()
        mock_count.return_value = 1

        self.assertTrue(processor._torrent_has_seeders(99))
        mock_sleep.assert_not_called()

    @patch('nefarious.processors.count_live_seeders')
    @patch('nefarious.processors.time.sleep')
    def test_no_seeders_returns_false_after_wait(self, mock_sleep, mock_count):
        processor = WatchProcessorBase.__new__(WatchProcessorBase)
        processor.transmission_client = Mock()
        mock_count.return_value = 0

        self.assertFalse(processor._torrent_has_seeders(99))
        # polls every 5s for up to 60s => 12 attempts
        self.assertEqual(mock_count.call_count, 12)


class FetchFallbackTest(TestCase):
    @patch('nefarious.processors.apps.get_model')
    @patch('nefarious.processors.TorrentBlacklist')
    @patch('nefarious.processors.get_transmission_client')
    def test_tries_next_result_when_no_live_seeders(self, mock_get_client, mock_blacklist, mock_get_model):
        mock_blacklist.objects.filter.return_value.exists.return_value = False
        mock_get_model.return_value.objects.filter.return_value.exists.return_value = True

        client = Mock()
        client.get_session.return_value = Mock()
        torrent = Mock()
        torrent.id = 99
        torrent.hashString = 'abc123'
        torrent.name = 'Best Torrent'
        client.add_torrent.return_value = torrent
        mock_get_client.return_value = client

        processor = WatchProcessorBase.__new__(WatchProcessorBase)
        processor.nefarious_settings = Mock()
        processor.transmission_client = client
        processor.watch_media = Mock()
        processor.watch_media.release_date = None
        processor.watch_media.id = 1
        processor.watch_media._meta.object_name = 'WatchMovie'
        processor._get_search_results = Mock(return_value=Mock(
            ok=True,
            results=[
                {'Title': 'Stale Seeders', 'Seeders': 94, 'Size': 0, 'Guid': 'g1', 'torrent_url': 'magnet:a'},
                {'Title': 'Healthy', 'Seeders': 7, 'Size': 0, 'Guid': 'g2', 'torrent_url': 'magnet:b'},
            ],
        ))
        processor.is_match = Mock(return_value=True)
        processor._results_with_valid_urls = Mock(side_effect=lambda results: results)
        processor._get_download_dir = Mock(return_value='/downloads/tv')
        processor._torrent_has_seeders = Mock(side_effect=[False, True])
        processor._save_torrent_details = Mock()
        processor._set_last_attempt_date = Mock()

        self.assertTrue(processor.fetch())

        # added the first (dead) result, removed it, then added the second and committed it
        self.assertEqual(client.add_torrent.call_count, 2)
        self.assertEqual(client.start_torrent.call_count, 2)
        client.remove_torrent.assert_called_once_with([99])
        self.assertEqual(processor._save_torrent_details.call_count, 1)
        self.assertEqual(processor._torrent_has_seeders.call_count, 2)
