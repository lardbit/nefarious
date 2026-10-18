from unittest.mock import Mock, patch

from nefarious.parsers.tv import TVParser
from nefarious.processors import WatchTVSeasonProcessor
from nefarious.search import SearchTorrentsCombined
from django.test import TestCase


class TVMatch(TestCase):
    tv_season_tests = []

    def setUp(self):
        # full season tests
        self.tv_season_tests = [
            ("Atlanta.S02.720p.AMZN.WEBRip.DDP5.1.x264-NTb[rartv]", "Atlanta", 2),
            ("30.Rock.Season.04.HDTV.XviD-DIMENSION", "30 Rock", 4),
            ("Parks.and.Recreation.S02.720p.x264-DIMENSION", "Parks and Recreation", 2),
            ("The.Office.US.S03.720p.x264-DIMENSION", "The Office US", 3),
            ("Sons.of.Anarchy.S03.720p.BluRay-CLUE\REWARD", "Sons of Anarchy", 3),
            ("Adventure Time S02 720p HDTV x264 CRON", "Adventure Time", 2),
            ("Sealab.2021.S04.iNTERNAL.DVDRip.XviD-VCDVaULT", "Sealab 2021", 4),
            ("Hawaii Five 0 S01 720p WEB DL DD5 1 H 264 NT", "Hawaii Five 0", 1),
            ("30 Rock S03 WS PDTV XviD FUtV", "30 Rock", 3),
            ("The Office Season 4 WS PDTV XviD FUtV", "The Office", 4),
            ("Eureka Season 1 720p WEB DL DD 5 1 h264 TjHD", "Eureka", 1),
            ("The Office Season4 WS PDTV XviD FUtV", "The Office", 4),
            ("Eureka S 01 720p WEB DL DD 5 1 h264 TjHD", "Eureka", 1),
            ("Doctor Who Confidential   Season 3", "Doctor Who Confidential", 3),
            ("Fleming.S01.720p.WEBDL.DD5.1.H.264-NTb", "Fleming", 1),
            ("Holmes.Makes.It.Right.S02.720p.HDTV.AAC5.1.x265-NOGRP", "Holmes Makes It Right", 2),
            ("My.Series.S2014.720p.HDTV.x264-ME", "My Series", 2014),
        ]

    def test_tv(self):
        for name, title, season in self.tv_season_tests:
            parser = TVParser(name)
            self.assertTrue(parser.is_match(title, season), '{} ({})'.format(name, parser.match))


class TVSeasonYearMatch(TestCase):
    def test_missing_year_in_torrent_still_matches(self):
        parser = TVParser('Scrubs S01 DVDRip x264')
        self.assertTrue(parser.is_match('Scrubs', 1, year='2001'))


class WatchTVSeasonSearch(TestCase):
    @patch('nefarious.processors.SearchTorrents')
    def test_get_search_results_queries_title_and_season(self, mock_search):
        queries = []

        def fake(media_type, query):
            queries.append(query)
            result = Mock()
            result.ok = True
            result.results = []
            result.error_content = ''
            return result

        mock_search.side_effect = fake

        processor = WatchTVSeasonProcessor.__new__(WatchTVSeasonProcessor)
        processor.tmdb_media = {'name': 'Scrubs'}
        processor.watch_media = Mock(season_number=1)

        result = processor._get_search_results()

        self.assertIsInstance(result, SearchTorrentsCombined)
        self.assertEqual(queries, ['Scrubs', 'Scrubs s01'])


class WatchTVSeasonProcessorMatch(TestCase):
    def test_is_match_without_year(self):
        processor = WatchTVSeasonProcessor.__new__(WatchTVSeasonProcessor)
        processor.tmdb_media = {'name': 'Scrubs', 'first_air_date': '2001-10-02'}
        processor.watch_media = Mock(season_number=1)
        parser = TVParser('Scrubs S01 (2001) - 2160p HDR Ai Upscale 2.0 MultiSub MKV -Mesc')
        self.assertTrue(processor._is_match(parser))
