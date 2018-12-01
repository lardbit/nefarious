from nefarious.parsers.base import ParserBase
from nefarious import quality
from django.test import TestCase


class QualityMatch(TestCase):
    quality_tests = []

    def setUp(self):
        self.quality_tests = [
            # sd quality tests
            ("S07E23 .avi ", quality.SDTV),
            ("The.Shield.S01E13.x264-CtrlSD", quality.SDTV),
            ("Nikita S02E01 HDTV XviD 2HD", quality.SDTV),
            ("Gossip Girl S05E11 PROPER HDTV XviD 2HD", quality.SDTV),
            ("The Jonathan Ross Show S02E08 HDTV x264 FTP", quality.SDTV),
            ("White.Van.Man.2011.S02E01.WS.PDTV.x264-TLA", quality.SDTV),
            ("White.Van.Man.2011.S02E01.WS.PDTV.x264-REPACK-TLA", quality.SDTV),
            ("The Real Housewives of Vancouver S01E04 DSR x264 2HD", quality.SDTV),
            ("Vanguard S01E04 Mexicos Death Train DSR x264 MiNDTHEGAP", quality.SDTV),
            ("Chuck S11E03 has no periods or extension HDTV", quality.SDTV),
            ("Chuck.S04E05.HDTV.XviD-LOL", quality.SDTV),
            ("Sonny.With.a.Chance.S02E15.avi", quality.SDTV),
            ("Sonny.With.a.Chance.S02E15.xvid", quality.SDTV),
            ("Sonny.With.a.Chance.S02E15.divx", quality.SDTV),
            ("The.Girls.Next.Door.S03E06.HDTV-WiDE", quality.SDTV),
            ("Degrassi.S10E27.WS.DSR.XviD-2HD", quality.SDTV),
            ("[HorribleSubs] Yowamushi Pedal - 32 [480p]", quality.SDTV),
            ("[CR] Sailor Moon - 004 [480p][48CE2D0F]", quality.SDTV),
            ("[Hatsuyuki] Naruto Shippuuden - 363 [848x480][ADE35E38]", quality.SDTV),
            ("Muppet.Babies.S03.TVRip.XviD-NOGRP", quality.SDTV),

            # dvd
            ("WEEDS.S03E01-06.DUAL.XviD.Bluray.AC3-REPACK.-HELLYWOOD.avi", quality.DVD),
            ("The.Shield.S01E13.NTSC.x264-CtrlSD", quality.DVD),
            ("WEEDS.S03E01-06.DUAL.BDRip.XviD.AC3.-HELLYWOOD", quality.DVD),
            ("WEEDS.S03E01-06.DUAL.BDRip.X-viD.AC3.-HELLYWOOD", quality.DVD),
            ("WEEDS.S03E01-06.DUAL.BDRip.AC3.-HELLYWOOD", quality.DVD),
            ("WEEDS.S03E01-06.DUAL.BDRip.XviD.AC3.-HELLYWOOD.avi", quality.DVD),
            ("WEEDS.S03E01-06.DUAL.XviD.Bluray.AC3.-HELLYWOOD.avi", quality.DVD),
            ("The.Girls.Next.Door.S03E06.DVDRip.XviD-WiDE", quality.DVD),
            ("The.Girls.Next.Door.S03E06.DVD.Rip.XviD-WiDE", quality.DVD),
            ("the.shield.1x13.circles.ws.xvidvd-tns", quality.DVD),
            # TODO - the "source_regex" word boundaries don't work with the surrounding underscores,.ie "_dvdrip_"
            #("the_x-files.9x18.sunshine_days.ac3.ws_dvdrip_xvid-fov.avi", quality.DVD),
            ("[FroZen] Miyuki - 23 [DVD][7F6170E6]", quality.DVD),
            ("Hannibal.S01E05.576p.BluRay.DD5.1.x264-HiSD", quality.DVD),
            ("Hannibal.S01E05.480p.BluRay.DD5.1.x264-HiSD", quality.DVD),
            ("Heidi Girl of the Alps (BD)(640x480(RAW) (BATCH 1) (1-13)", quality.DVD),
            ("[Doki] Clannad - 02 (848x480 XviD BD MP3) [95360783]", quality.DVD),
        ]

    def test_movie(self):
        for name, expected_quality in self.quality_tests:
            parser = ParserBase(name)
            parser_quality = parser.parse_quality(name)
            self.assertTrue(parser_quality == expected_quality, '{} : {} != {}'.format(name, parser_quality, expected_quality))
