from nefarious.parsers.base import ParserBase
from nefarious import quality
from django.test import TestCase


class QualityMatch(TestCase):
    sd_quality_tests = []

    def setUp(self):
        # sd quality tests
        self.sd_quality_tests = [
            "S07E23 .avi ",
            "The.Shield.S01E13.x264-CtrlSD",
            "Nikita S02E01 HDTV XviD 2HD",
            "Gossip Girl S05E11 PROPER HDTV XviD 2HD",
            "The Jonathan Ross Show S02E08 HDTV x264 FTP",
            "White.Van.Man.2011.S02E01.WS.PDTV.x264-TLA",
            "White.Van.Man.2011.S02E01.WS.PDTV.x264-REPACK-TLA",
            "The Real Housewives of Vancouver S01E04 DSR x264 2HD",
            "Vanguard S01E04 Mexicos Death Train DSR x264 MiNDTHEGAP",
            "Chuck S11E03 has no periods or extension HDTV",
            "Chuck.S04E05.HDTV.XviD-LOL",
            "Sonny.With.a.Chance.S02E15.avi",
            "Sonny.With.a.Chance.S02E15.xvid",
            "Sonny.With.a.Chance.S02E15.divx",
            "The.Girls.Next.Door.S03E06.HDTV-WiDE",
            "Degrassi.S10E27.WS.DSR.XviD-2HD",
            "[HorribleSubs] Yowamushi Pedal - 32 [480p]",
            "[CR] Sailor Moon - 004 [480p][48CE2D0F]",
            "[Hatsuyuki] Naruto Shippuuden - 363 [848x480][ADE35E38]",
            "Muppet.Babies.S03.TVRip.XviD-NOGRP",
        ]

    def test_movie(self):
        for name in self.sd_quality_tests:
            parser = ParserBase(name)
            parser_quality = parser.parse_quality(name)
            self.assertTrue(parser_quality == quality.SDTV, '{} : {}'.format(name, parser_quality))
