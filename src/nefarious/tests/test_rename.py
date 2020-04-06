from datetime import datetime
from nefarious.models import WatchMovie, WatchTVSeason, WatchTVShow, WatchTVEpisode
from django.test import TestCase
from nefarious.utils import get_media_new_path_and_name


class RenameTorrentsAndPaths(TestCase):
    tests = []

    def setUp(self):
        movie = WatchMovie(name='Rambo', release_date=datetime(1982, 1, 1))
        movie_with_colon = WatchMovie(name='The Lego Movie 2: The Second Part', release_date=datetime(2019, 1, 1))
        show = WatchTVShow(name='Rick and Morty')
        season = WatchTVSeason(watch_tv_show=show, season_number=1)
        episode = WatchTVEpisode(watch_tv_show=show, season_number=1, episode_number=14)
        self.tests = [
            # movie folder
            (movie, "Rambo.1982.1080p.BluRay", None, "Rambo (1982)", False),
            # movie single file
            (movie, "Rambo.1982.1080p.BluRay.mkv", "Rambo (1982)", "Rambo (1982).mkv", True),
            # movie folder with a colon in the name which should be replaced with a hyphen
            (movie_with_colon, "The.Lego.Movie.2:The.Second.Part", None, "The Lego Movie 2 - The Second Part (2019)", False),
            # full season
            (season, "Rick.and.Morty.S01.720p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]", "Rick and Morty", "Rick and Morty - Season 01", False),
            # single episode folder
            (episode, "Rick.and.Morty.S01E14.720p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]", "Rick and Morty/Season 01", "Rick and Morty - S01E14", False),
            # single episode single file
            (episode, "Rick.and.Morty.S01E14.720p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv].mkv", "Rick and Morty/Season 01", "Rick and Morty - S01E14.mkv", True),
        ]

    def test_rename(self):
        for test_media, test_torrent, test_path, test_name, is_single_file in self.tests:
            path, name = get_media_new_path_and_name(test_media, test_torrent, is_single_file)
            self.assertEquals(test_name, name)
            self.assertEquals(test_path, path)
