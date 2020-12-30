from nefarious.models import WatchTVShow, WatchTVSeason
from nefarious.parsers.tv import TVParser
from django.test import TestCase


class AccentTest(TestCase):
    # test fuzzy accent matching

    tests = []

    def setUp(self):
        self.tests = [
            # torrent / media / equality
            (
                "Erase Una Vez S01 SPANISH SDTV XviD",
                WatchTVSeason(watch_tv_show=WatchTVShow(name='Érase Una Vez'), season_number=1),
                True,
            ),
        ]

    def test_results(self):
        for name, media, equality in self.tests:
            parser = TVParser(name)
            self.assertEqual(
                parser.is_match(str(media.watch_tv_show), season_number=media.season_number),
                equality,
                '{} ({})'.format(name, parser.match)
            )
