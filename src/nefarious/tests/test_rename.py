from datetime import datetime
from nefarious.models import WatchMovie, WatchTVSeason, WatchTVShow, WatchTVEpisode
from django.test import TestCase
from nefarious.utils import get_media_new_name_and_path


class RenameTorrentPaths(TestCase):
    tests = []

    def setUp(self):
        movie = WatchMovie(name='Rambo', release_date=datetime(1982, 1, 1))
        show = WatchTVShow(name='Rick and Morty')
        season = WatchTVSeason(watch_tv_show=show, season_number=1)
        episode = WatchTVEpisode(watch_tv_show=show, season_number=1, episode_number=14)
        self.tests = [
            # movie folder
            (movie, "Rambo.1982.1080p.BluRay", "Rambo (1982)", "Rambo (1982)", False),
            # movie single file
            (movie, "Rambo.1982.1080p.BluRay.mkv", "Rambo (1982).mkv", "Rambo (1982)", True),
            # full season
            (season, "Rick.and.Morty.S01.720p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]", "Season 01", "Rick and Morty", False),
            # single episode folder
            (episode, "Rick.and.Morty.S01E14.720p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]", "S01E14", "Rick and Morty/Season 01", False),
            # single episode single file
            (episode, "Rick.and.Morty.S01E14.720p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv].mkv", "S01E14.mkv", "Rick and Morty/Season 01", True),
        ]

    def test_tv(self):
        for test_media, test_torrent, test_name, test_path, is_single_file in self.tests:
            name, path = get_media_new_name_and_path(test_media, test_torrent, is_single_file)
            self.assertEquals(test_name, name)
            self.assertEquals(test_path, path)
