from nefarious.parsers.base import ParserBase
from nefarious import quality
from django.test import TestCase


class QualityMatch(TestCase):
    sd_quality_tests = []

    def setUp(self):
        # sd quality tests
        self.sd_quality_tests = [
            ("S07E23 .avi ", False),
            ("The.Shield.S01E13.x264-CtrlSD", False),
            ("Nikita S02E01 HDTV XviD 2HD", False),
            ("Gossip Girl S05E11 PROPER HDTV XviD 2HD", True),
            ("The Jonathan Ross Show S02E08 HDTV x264 FTP", False),
            ("White.Van.Man.2011.S02E01.WS.PDTV.x264-TLA", False),
            ("White.Van.Man.2011.S02E01.WS.PDTV.x264-REPACK-TLA", True),
            ("The Real Housewives of Vancouver S01E04 DSR x264 2HD", False),
            ("Vanguard S01E04 Mexicos Death Train DSR x264 MiNDTHEGAP", False),
            ("Chuck S11E03 has no periods or extension HDTV", False),
            ("Chuck.S04E05.HDTV.XviD-LOL", False),
            ("Sonny.With.a.Chance.S02E15.avi", False),
            ("Sonny.With.a.Chance.S02E15.xvid", False),
            ("Sonny.With.a.Chance.S02E15.divx", False),
            ("The.Girls.Next.Door.S03E06.HDTV-WiDE", False),
            ("Degrassi.S10E27.WS.DSR.XviD-2HD", False),
            ("[HorribleSubs] Yowamushi Pedal - 32 [480p]", False),
            ("[CR] Sailor Moon - 004 [480p][48CE2D0F]", False),
            ("[Hatsuyuki] Naruto Shippuuden - 363 [848x480][ADE35E38]", False),
            ("Muppet.Babies.S03.TVRip.XviD-NOGRP", False),
        ]

    def test_movie(self):
        pass
        #for name, is_match in self.sd_quality_tests:
        #    parser = ParserBase(name)
        #    if is_match and parser.parse_quality(name) != quality.SDTV:
        #        print('==============')
        #        print(name)
        #        print(parser.parse_quality(name).name)
        #        print('==============')
        #    elif not is_match and parser.parse_quality(name) == quality.SDTV:
        #        print('====not======')
        #        print(name)
        #        print(parser.parse_quality(name).name)
        #        print('==============')
        #    self.assertEqual(parser.parse_quality(name) == quality.SDTV, is_match)
