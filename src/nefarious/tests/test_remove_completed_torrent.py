from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from nefarious import quality
from nefarious.models import MEDIA_TYPE_MOVIE, NefariousSettings, QualityProfile, WatchMovie
from nefarious.tasks import remove_completed_torrent_task


class RemoveCompletedTorrentTaskTest(TestCase):

    def setUp(self):
        quality_profile = QualityProfile.objects.create(
            name=quality.SDTV,
            quality=quality.SDTV,
        )
        self.nefarious_settings = NefariousSettings.objects.create(
            quality_profile_tv=quality_profile,
            quality_profile_movies=quality_profile,
        )
        self.user = User.objects.create_superuser('test', 'test@test.com', 'test')
        self.watch_movie = WatchMovie.objects.create(
            user=self.user,
            tmdb_movie_id=1,
            name='Test Movie',
            poster_image_url='',
            transmission_torrent_hash='abc123',
            transmission_torrent_name='Test Movie Torrent',
        )

    @patch('nefarious.tasks.get_transmission_client')
    def test_remove_completed_torrent_is_disabled_by_default(self, get_transmission_client):
        remove_completed_torrent_task(MEDIA_TYPE_MOVIE, self.watch_movie.id)

        get_transmission_client.assert_not_called()
        self.watch_movie.refresh_from_db()
        self.assertEqual('abc123', self.watch_movie.transmission_torrent_hash)
        self.assertEqual('Test Movie Torrent', self.watch_movie.transmission_torrent_name)

    @patch('nefarious.tasks.get_transmission_client')
    def test_remove_completed_torrent_removes_from_transmission_without_deleting_data(self, get_transmission_client):
        transmission_client = Mock()
        get_transmission_client.return_value = transmission_client
        self.nefarious_settings.remove_completed_torrents_from_transmission = True
        self.nefarious_settings.save()

        remove_completed_torrent_task(MEDIA_TYPE_MOVIE, self.watch_movie.id)

        transmission_client.remove_torrent.assert_called_once_with(['abc123'], delete_data=False, timeout=10)
        self.watch_movie.refresh_from_db()
        self.assertIsNone(self.watch_movie.transmission_torrent_hash)
        self.assertIsNone(self.watch_movie.transmission_torrent_name)
