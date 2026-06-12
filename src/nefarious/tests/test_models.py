from django.test import TestCase
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from nefarious.models import (
    NefariousSettings, QualityProfile, WatchMovie, WatchTVShow,
    WatchTVSeason, WatchTVSeasonRequest, WatchTVEpisode, TorrentBlacklist,
    MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV_SHOW,
)
from nefarious import quality


class QualityProfileModelTest(TestCase):
    def test_create_quality_profile(self):
        qp = QualityProfile.objects.create(name='HD 1080p', quality=quality.PROFILE_HD_1080p)
        self.assertEqual(str(qp), 'HD 1080p (hd-1080p)')

    def test_unique_name_constraint(self):
        QualityProfile.objects.create(name='Test', quality=quality.PROFILE_ANY)
        with self.assertRaises(IntegrityError):
            QualityProfile.objects.create(name='Test', quality=quality.PROFILE_HD_1080p)

    def test_str_method_shows_quality(self):
        qp = QualityProfile.objects.create(name='Custom', quality=quality.PROFILE_HD_1080p)
        self.assertIn('1080p', str(qp))

    def test_str_method_omits_quality_when_same_as_name(self):
        qp = QualityProfile.objects.create(name='hd-1080p-test', quality=quality.PROFILE_HD_1080p)
        self.assertEqual(str(qp), 'hd-1080p-test (hd-1080p)')

    def test_min_size_gb_null_by_default(self):
        qp = QualityProfile.objects.create(name='Any', quality=quality.PROFILE_ANY)
        self.assertIsNone(qp.min_size_gb)
        self.assertIsNone(qp.max_size_gb)

    def test_max_size_gb_validator(self):
        from django.core.exceptions import ValidationError
        qp = QualityProfile(name='Test', quality=quality.PROFILE_ANY, max_size_gb=-1)
        with self.assertRaises(ValidationError):
            qp.full_clean()


class NefariousSettingsModelTest(TestCase):
    def setUp(self):
        self.qp_tv = QualityProfile.objects.create(name='TV Profile', quality=quality.PROFILE_ANY)
        self.qp_movie = QualityProfile.objects.create(name='Movie Profile', quality=quality.PROFILE_HD_1080p)

    def test_singleton_get_raises_for_multiple(self):
        NefariousSettings.objects.create(
            quality_profile_tv=self.qp_tv,
            quality_profile_movies=self.qp_movie,
        )
        NefariousSettings.objects.create(
            quality_profile_tv=self.qp_tv,
            quality_profile_movies=self.qp_movie,
        )
        with self.assertRaises(Exception):
            NefariousSettings.get()

    def test_get_returns_single_instance(self):
        ns = NefariousSettings.objects.create(
            quality_profile_tv=self.qp_tv,
            quality_profile_movies=self.qp_movie,
        )
        self.assertEqual(NefariousSettings.get(), ns)

    def test_default_values(self):
        ns = NefariousSettings.objects.create(
            quality_profile_tv=self.qp_tv,
            quality_profile_movies=self.qp_movie,
        )
        self.assertEqual(ns.language, 'en')
        self.assertEqual(ns.jackett_host, 'jackett')
        self.assertEqual(ns.jackett_port, 9117)
        self.assertEqual(ns.jackett_token, NefariousSettings.JACKETT_TOKEN_DEFAULT)
        self.assertEqual(ns.transmission_host, 'transmission')
        self.assertEqual(ns.transmission_port, 9091)
        self.assertFalse(ns.allow_hardcoded_subs)
        self.assertFalse(ns.enable_video_detection)
        self.assertFalse(ns.open_subtitles_auto)
        self.assertFalse(ns.stuck_download_handling_enabled)
        self.assertEqual(ns.stuck_download_handling_days, 3)

    def test_should_save_subtitles_false_when_not_configured(self):
        ns = NefariousSettings.objects.create(
            quality_profile_tv=self.qp_tv,
            quality_profile_movies=self.qp_movie,
        )
        self.assertFalse(ns.should_save_subtitles())

    def test_should_save_subtitles_true_when_configured(self):
        ns = NefariousSettings.objects.create(
            quality_profile_tv=self.qp_tv,
            quality_profile_movies=self.qp_movie,
            open_subtitles_auto=True,
            open_subtitles_user_token='token123',
        )
        self.assertTrue(ns.should_save_subtitles())

    def test_get_tmdb_poster_url(self):
        ns = NefariousSettings(
            quality_profile_tv=self.qp_tv,
            quality_profile_movies=self.qp_movie,
            tmdb_configuration={'images': {'secure_base_url': 'https://image.tmdb.org/t/p/'}},
        )
        url = ns.get_tmdb_poster_url('/abc/poster.jpg')
        self.assertEqual(url, 'https://image.tmdb.org/t/p/original/abc/poster.jpg')


class WatchMovieModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.qp = QualityProfile.objects.create(name='HD', quality=quality.PROFILE_HD_1080p)

    def test_create_watch_movie(self):
        movie = WatchMovie.objects.create(
            user=self.user,
            tmdb_movie_id=12345,
            name='Test Movie',
            poster_image_url='http://example.com/poster.jpg',
            quality_profile=self.qp,
        )
        self.assertEqual(str(movie), 'Test Movie')
        self.assertFalse(movie.collected)
        self.assertEqual(movie.tmdb_movie_id, 12345)

    def test_unique_tmdb_movie_id(self):
        WatchMovie.objects.create(
            user=self.user, tmdb_movie_id=123, name='Movie 1',
            poster_image_url='http://a.com/1.jpg',
        )
        with self.assertRaises(IntegrityError):
            WatchMovie.objects.create(
                user=self.user, tmdb_movie_id=123, name='Movie 2',
                poster_image_url='http://a.com/2.jpg',
            )

    def test_collected_defaults_to_false(self):
        movie = WatchMovie.objects.create(
            user=self.user, tmdb_movie_id=999, name='New Movie',
            poster_image_url='http://a.com/p.jpg',
        )
        self.assertFalse(movie.collected)

    def test_quality_profile_can_be_null(self):
        movie = WatchMovie.objects.create(
            user=self.user, tmdb_movie_id=888, name='No Quality',
            poster_image_url='http://a.com/p.jpg',
            quality_profile=None,
        )
        self.assertIsNone(movie.quality_profile)

    def test_ordering_by_name(self):
        movie2 = WatchMovie.objects.create(
            user=self.user, tmdb_movie_id=2, name='B Movie',
            poster_image_url='http://a.com/b.jpg',
        )
        movie1 = WatchMovie.objects.create(
            user=self.user, tmdb_movie_id=1, name='A Movie',
            poster_image_url='http://a.com/a.jpg',
        )
        movies = list(WatchMovie.objects.all())
        self.assertEqual(movies[0].name, 'A Movie')
        self.assertEqual(movies[1].name, 'B Movie')


class WatchTVShowModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_create_watch_tv_show(self):
        show = WatchTVShow.objects.create(
            user=self.user,
            tmdb_show_id=12345,
            name='Test Show',
            poster_image_url='http://example.com/poster.jpg',
        )
        self.assertEqual(str(show), 'Test Show')
        self.assertEqual(show.tmdb_show_id, 12345)
        self.assertFalse(show.auto_watch)

    def test_unique_tmdb_show_id(self):
        WatchTVShow.objects.create(
            user=self.user, tmdb_show_id=123, name='Show 1',
            poster_image_url='http://a.com/1.jpg',
        )
        with self.assertRaises(IntegrityError):
            WatchTVShow.objects.create(
                user=self.user, tmdb_show_id=123, name='Show 2',
                poster_image_url='http://a.com/2.jpg',
            )


class WatchTVSeasonModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.show = WatchTVShow.objects.create(
            user=self.user, tmdb_show_id=100, name='Show',
            poster_image_url='http://a.com/p.jpg',
        )

    def test_create_season(self):
        season = WatchTVSeason.objects.create(
            user=self.user,
            watch_tv_show=self.show,
            season_number=1,
        )
        self.assertIn('Season 01', str(season))
        self.assertEqual(season.name, str(season))

    def test_season_deleted_when_show_deleted(self):
        WatchTVSeason.objects.create(
            user=self.user, watch_tv_show=self.show, season_number=1,
        )
        self.assertEqual(WatchTVSeason.objects.count(), 1)
        self.show.delete()
        self.assertEqual(WatchTVSeason.objects.count(), 0)

    def test_unique_show_season(self):
        WatchTVSeason.objects.create(
            user=self.user, watch_tv_show=self.show, season_number=1,
        )
        with self.assertRaises(IntegrityError):
            WatchTVSeason.objects.create(
                user=self.user, watch_tv_show=self.show, season_number=1,
            )


class WatchTVEpisodeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.show = WatchTVShow.objects.create(
            user=self.user, tmdb_show_id=100, name='Show',
            poster_image_url='http://a.com/p.jpg',
        )

    def test_create_episode(self):
        episode = WatchTVEpisode.objects.create(
            user=self.user,
            watch_tv_show=self.show,
            tmdb_episode_id=500,
            season_number=1,
            episode_number=5,
        )
        self.assertIn('S01E05', str(episode))
        self.assertEqual(episode.name, str(episode))

    def test_unique_show_season_episode(self):
        WatchTVEpisode.objects.create(
            user=self.user, watch_tv_show=self.show,
            tmdb_episode_id=1, season_number=1, episode_number=1,
        )
        with self.assertRaises(IntegrityError):
            WatchTVEpisode.objects.create(
                user=self.user, watch_tv_show=self.show,
                tmdb_episode_id=2, season_number=1, episode_number=1,
            )

    def test_episode_deleted_when_show_deleted(self):
        WatchTVEpisode.objects.create(
            user=self.user, watch_tv_show=self.show,
            tmdb_episode_id=1, season_number=1, episode_number=1,
        )
        self.assertEqual(WatchTVEpisode.objects.count(), 1)
        self.show.delete()
        self.assertEqual(WatchTVEpisode.objects.count(), 0)


class WatchTVSeasonRequestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.show = WatchTVShow.objects.create(
            user=self.user, tmdb_show_id=100, name='Show',
            poster_image_url='http://a.com/p.jpg',
        )

    def test_create_request(self):
        req = WatchTVSeasonRequest.objects.create(
            user=self.user,
            watch_tv_show=self.show,
            season_number=2,
        )
        self.assertIn('Season 02', str(req))

    def test_unique_show_season(self):
        WatchTVSeasonRequest.objects.create(
            user=self.user, watch_tv_show=self.show, season_number=1,
        )
        with self.assertRaises(IntegrityError):
            WatchTVSeasonRequest.objects.create(
                user=self.user, watch_tv_show=self.show, season_number=1,
            )


class TorrentBlacklistModelTest(TestCase):
    def test_create_blacklist_entry(self):
        entry = TorrentBlacklist.objects.create(
            hash='abc123def456',
            name='Bad Torrent',
        )
        self.assertEqual(str(entry), 'Bad Torrent: abc123def456')

    def test_unique_hash(self):
        TorrentBlacklist.objects.create(hash='aaa', name='First')
        with self.assertRaises(IntegrityError):
            TorrentBlacklist.objects.create(hash='aaa', name='Second')
