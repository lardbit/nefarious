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

            # webdl480
            ("Elementary.S01E10.The.Leviathan.480p.WEB-DL.x264-mSD", quality.WEBDL_480P),
            ("Glee.S04E10.Glee.Actually.480p.WEB-DL.x264-mSD", quality.WEBDL_480P),
            ("The.Big.Bang.Theory.S06E11.The.Santa.Simulation.480p.WEB-DL.x264-mSD", quality.WEBDL_480P),
            ("Da.Vincis.Demons.S02E04.480p.WEB.DL.nSD.x264-NhaNc3", quality.WEBDL_480P),
            ("Incorporated.S01E08.Das.geloeschte.Ich.German.Dubbed.DL.AmazonHD.x264-TVS", quality.WEBDL_480P),
            ("Haters.Back.Off.S01E04.Rod.Trip.mit.meinem.Onkel.German.DL.NetflixUHD.x264", quality.WEBDL_480P),

            # hdtv720
            ("Dexter - S01E01 - Title [HDTV]", quality.HDTV_720P),
            ("Dexter - S01E01 - Title [HDTV-720p]", quality.HDTV_720P),
            ("Pawn Stars S04E87 REPACK 720p HDTV x264 aAF", quality.HDTV_720P),
            ("Sonny.With.a.Chance.S02E15.720p", quality.HDTV_720P),
            ("S07E23 - [HDTV-720p].mkv ", quality.HDTV_720P),
            ("Chuck - S22E03 - MoneyBART - HD TV.mkv", quality.HDTV_720P),
            ("S07E23.mkv ", quality.HDTV_720P),
            ("Two.and.a.Half.Men.S08E05.720p.HDTV.X264-DIMENSION", quality.HDTV_720P),
            ("Sonny.With.a.Chance.S02E15.mkv", quality.HDTV_720P),
            ("Gem.Hunt.S01E08.Tourmaline.Nepal.720p.HDTV.x264-DHD", quality.HDTV_720P),
            ("[Underwater-FFF] No Game No Life - 01 (720p) [27AAA0A0]", quality.HDTV_720P),
            ("[Doki] Mahouka Koukou no Rettousei - 07 (1280x720 Hi10P AAC) [80AF7DDE]", quality.HDTV_720P),
            ("[Doremi].Yes.Pretty.Cure.5.Go.Go!.31.[1280x720].[C65D4B1F].mkv", quality.HDTV_720P),
            ("[HorribleSubs]_Fairy_Tail_-_145_[720p]", quality.HDTV_720P),
            ("[Eveyuu] No Game No Life - 10 [Hi10P 1280x720 H264][10B23BD8]", quality.HDTV_720P),
            ("Hells.Kitchen.US.S12E17.HR.WS.PDTV.X264-DIMENSION", quality.HDTV_720P),
            ("Survivorman.The.Lost.Pilots.Summer.HR.WS.PDTV.x264-DHD", quality.HDTV_720P),
            ("Victoria S01E07 - Motor zmen (CZ)[TvRip][HEVC][720p]", quality.HDTV_720P),
            ("flashpoint.S05E06.720p.HDTV.x264-FHD", quality.HDTV_720P),

            # hdtv1080
            ("Under the Dome S01E10 Let the Games Begin 1080p", quality.HDTV_1080P),
            ("DEXTER.S07E01.ARE.YOU.1080P.HDTV.X264-QCF", quality.HDTV_1080P),
            ("DEXTER.S07E01.ARE.YOU.1080P.HDTV.x264-QCF", quality.HDTV_1080P),
            ("DEXTER.S07E01.ARE.YOU.1080P.HDTV.proper.X264-QCF", quality.HDTV_1080P),
            ("Dexter - S01E01 - Title [HDTV-1080p]", quality.HDTV_1080P),
            ("[HorribleSubs] Yowamushi Pedal - 32 [1080p]", quality.HDTV_1080P),
            ("Victoria S01E07 - Motor zmen (CZ)[TvRip][HEVC][1080p]", quality.HDTV_1080P),
            ("Sword Art Online Alicization 04 vostfr FHD", quality.HDTV_1080P),
            ("Goblin Slayer 04 vostfr FHD.mkv", quality.HDTV_1080P),
            ("[Onii-ChanSub] SSSS.Gridman - 02 vostfr (FHD 1080p 10bits).mkv", quality.HDTV_1080P),
            ("[Miaou] Akanesasu Shoujo 02 VOSTFR FHD 10 bits", quality.HDTV_1080P),
            # TODO - the "resolution_regex" word boundaries don't work with the surrounding underscores,.ie "_FHD_"
            #("[mhastream.com]_Episode_05_FHD.mp4", quality.HDTV_1080P),
            ("[Kousei]_One_Piece_ - _609_[FHD][648A87C7].mp4", quality.HDTV_1080P),
            ("Presunto culpable 1x02 Culpabilidad [HDTV 1080i AVC MP2 2.0 Sub][GrupoHDS]", quality.HDTV_1080P),
            ("Cuéntame cómo pasó - 19x15 [344] Cuarenta años de baile [HDTV 1080i AVC MP2 2.0 Sub][GrupoHDS]", quality.HDTV_1080P),

            # hdtv2160
            ("My Title - S01E01 - EpTitle [HEVC 4k DTSHD-MA-6ch]", quality.HDTV_2160P),
            ("My Title - S01E01 - EpTitle [HEVC-4k DTSHD-MA-6ch]", quality.HDTV_2160P),
            ("My Title - S01E01 - EpTitle [4k HEVC DTSHD-MA-6ch]", quality.HDTV_2160P),
        ]

    def test_movie(self):
        for name, expected_quality in self.quality_tests:
            parser = ParserBase(name)
            parser_quality = parser.parse_quality(name)
            self.assertTrue(parser_quality == expected_quality, '{} : {} != {}'.format(name, parser_quality, expected_quality))
