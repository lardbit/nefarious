import os

from django.contrib.auth.models import User
from django.test import TestCase
from nefarious.models import NefariousSettings, WatchTVShow, WatchTVEpisode
from nefarious.importer.tv import TVImporter
from nefarious.tmdb import get_tmdb_client


class TVImportTest(TestCase):
    tv_tests = []

    def setUp(self):
        self.tv_tests = [
            # file path, title, season, episode
            ("Atlanta Season 2 Mp4 1080p/Atlanta.S02E04.720p.AMZN.WEBRip.x264-GalaxyTV.mkv", "Atlanta", 2, 4),
            ("Atlanta Season 2 Mp4 1080p/Read Me.txt", False),
            ("American.Crime.Story.S01E04.HDTV.x264-KILLERS[ettv]/Torrent-Downloaded-from-ExtraTorrent.cc.txt", False),
            ("American.Crime.Story.S01E04.HDTV.x264-KILLERS[ettv]/American.Crime.Story.S01E04.HDTV.x264-KILLERS[ettv].mp4", "American Crime Story", 1, 4),
            ("Insecure/S02E01.mkv", "Insecure", 2, 1),
            ("Insecure/Season 01/S01E01.mkv", "Insecure", 1, 1),
            ("Some.Show.S01E01.mkv", False),  # fake show
            ("The Dog Whisperer Season 1/1x24 - Lucy and Lizzie.avi", 'Dog Whisperer', 1, 24),
            ("Some.Show.S01E01", False),
            ("Some.Show.S01E01.fake", False),
            ("Deadwood - Season 2/S02E01 - A Lie Agreed Upon (1) - Ehhhh.mkv", "Deadwood", 2, 1),
            ("Avenue 5/Avenue 5 - Season 01/Avenue.5.S01E04.720p.AMZN.WEBRip.x264-GalaxyTV.mkv", "Avenue 5", 1, 4),
            ("Avenue 5/Avenue 5 - Season 01/[TGx]Downloaded from torrentgalaxy.to .txt", False),
        ]

    def test_tv(self):
        # populate some required data
        nefarious_settings = NefariousSettings()
        # required tmdb config data for saving models
        nefarious_settings.tmdb_configuration = {
            'images': {
                'secure_base_url': 'https://image.tmdb.org/t/p/',
            },
        }
        tmdb_client = get_tmdb_client(nefarious_settings)
        # use the first super user account to assign media
        user = User.objects.create_superuser('test', 'test@test.com', 'test')

        # import
        importer = TVImporter(
            nefarious_settings=nefarious_settings,
            root_path='/test-download',
            tmdb_client=tmdb_client,
            user=user,
        )
        for test_result in self.tv_tests:
            # prepend '/tv' to the test path
            test_path = os.path.join('/tv', test_result[0])
            import_result = importer.ingest_path(test_path)
            if test_result[1] is False or import_result is False:
                self.assertEqual(test_result[1], import_result, '{} != {}'.format(test_result[1], import_result))
            else:
                show = WatchTVShow(name=test_result[1])
                episode = WatchTVEpisode(watch_tv_show=show, season_number=test_result[2], episode_number=test_result[3])
                self.assertTrue(episode.watch_tv_show.name == import_result.watch_tv_show.name,
                                '{} != {}'.format(episode.watch_tv_show.name, import_result.watch_tv_show.name))
                self.assertTrue(episode.season_number == import_result.season_number,
                                '{} != {}'.format(episode.season_number, import_result.season_number))
                self.assertTrue(episode.episode_number == import_result.episode_number,
                                '{} != {}'.format(episode.episode_number, import_result.episode_number))
