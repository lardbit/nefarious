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

            # webdl720
            ("Arrested.Development.S04E01.720p.WEBRip.AAC2.0.x264-NFRiP", quality.WEBDL_720P),
            ("Vanguard S01E04 Mexicos Death Train 720p WEB DL", quality.WEBDL_720P),
            ("Hawaii Five 0 S02E21 720p WEB DL DD5 1 H 264", quality.WEBDL_720P),
            ("Castle S04E22 720p WEB DL DD5 1 H 264 NFHD", quality.WEBDL_720P),
            ("Chuck - S11E06 - D-Yikes! - 720p WEB-DL.mkv", quality.WEBDL_720P),
            ("Sonny.With.a.Chance.S02E15.720p.WEB-DL.DD5.1.H.264-SURFER", quality.WEBDL_720P),
            ("S07E23 - [WEBDL].mkv ", quality.WEBDL_720P),
            ("Fringe S04E22 720p WEB-DL DD5.1 H264-EbP.mkv", quality.WEBDL_720P),
            ("House.S04.720p.Web-Dl.Dd5.1.h264-P2PACK", quality.WEBDL_720P),
            ("Da.Vincis.Demons.S02E04.720p.WEB.DL.nSD.x264-NhaNc3", quality.WEBDL_720P),
            ("CSI.Miami.S04E25.720p.iTunesHD.AVC-TVS", quality.WEBDL_720P),
            ("Castle.S06E23.720p.WebHD.h264-euHD", quality.WEBDL_720P),
            ("The.Nightly.Show.2016.03.14.720p.WEB.x264-spamTV", quality.WEBDL_720P),
            ("The.Nightly.Show.2016.03.14.720p.WEB.h264-spamTV", quality.WEBDL_720P),
            ("Incorporated.S01E08.Das.geloeschte.Ich.German.DD51.Dubbed.DL.720p.AmazonHD.x264-TVS", quality.WEBDL_720P),
            ("Marco.Polo.S01E11.One.Hundred.Eyes.2015.German.DD51.DL.720p.NetflixUHD.x264.NewUp.by.Wunschtante", quality.WEBDL_720P),
            ("Hush 2016 German DD51 DL 720p NetflixHD x264-TVS", quality.WEBDL_720P),
            ("Community.6x10.Basic.RV.Repair.and.Palmistry.ITA.ENG.720p.WEB-DLMux.H.264-GiuseppeTnT", quality.WEBDL_720P),
            ("Community.6x11.Modern.Espionage.ITA.ENG.720p.WEB.DLMux.H.264-GiuseppeTnT", quality.WEBDL_720P),

            # webdl1080
            ("Arrested.Development.S04E01.iNTERNAL.1080p.WEBRip.x264-QRUS", quality.WEBDL_1080P),
            ("CSI NY S09E03 1080p WEB DL DD5 1 H264 NFHD", quality.WEBDL_1080P),
            ("Two and a Half Men S10E03 1080p WEB DL DD5 1 H 264 NFHD", quality.WEBDL_1080P),
            ("Criminal.Minds.S08E01.1080p.WEB-DL.DD5.1.H264-NFHD", quality.WEBDL_1080P),
            ("Its.Always.Sunny.in.Philadelphia.S08E01.1080p.WEB-DL.proper.AAC2.0.H.264", quality.WEBDL_1080P),
            ("Two and a Half Men S10E03 1080p WEB DL DD5 1 H 264 REPACK NFHD", quality.WEBDL_1080P),
            ("Glee.S04E09.Swan.Song.1080p.WEB-DL.DD5.1.H.264-ECI", quality.WEBDL_1080P),
            ("The.Big.Bang.Theory.S06E11.The.Santa.Simulation.1080p.WEB-DL.DD5.1.H.264", quality.WEBDL_1080P),
            ("Rosemary's.Baby.S01E02.Night.2.[WEBDL-1080p].mkv", quality.WEBDL_1080P),
            ("The.Nightly.Show.2016.03.14.1080p.WEB.x264-spamTV", quality.WEBDL_1080P),
            ("The.Nightly.Show.2016.03.14.1080p.WEB.h264-spamTV", quality.WEBDL_1080P),
            ("Psych.S01.1080p.WEB-DL.AAC2.0.AVC-TrollHD", quality.WEBDL_1080P),
            ("Series Title S06E08 1080p WEB h264-EXCLUSIVE", quality.WEBDL_1080P),
            ("Series Title S06E08 No One PROPER 1080p WEB DD5 1 H 264-EXCLUSIVE", quality.WEBDL_1080P),
            ("Series Title S06E08 No One PROPER 1080p WEB H 264-EXCLUSIVE", quality.WEBDL_1080P),
            # TODO - "source_regex" captures "PAL" (ie. dvd group) and "webdl" comes up blank.
            #        look into regex library as I believe it's only returning a single result vs all groups
            #("The.Simpsons.S25E21.Pay.Pal.1080p.WEB-DL.DD5.1.H.264-NTb", quality.WEBDL_1080P),
            ("Incorporated.S01E08.Das.geloeschte.Ich.German.DD51.Dubbed.DL.1080p.AmazonHD.x264-TVS", quality.WEBDL_1080P),
            ("Death.Note.2017.German.DD51.DL.1080p.NetflixHD.x264-TVS", quality.WEBDL_1080P),
            ("Played.S01E08.Pro.Gamer.1440p.BKPL.WEB-DL.H.264-LiGHT", quality.WEBDL_1080P),
            ("Good.Luck.Charlie.S04E11.Teddy's.Choice.FHD.1080p.Web-DL", quality.WEBDL_1080P),
            ("Outlander.S04E03.The.False.Bride.1080p.NF.WEB.DDP5.1.x264-NTb[rartv]", quality.WEBDL_1080P),

            # webdl2160
            ("CASANOVA S01E01.2160P AMZN WEBRIP DD2.0 HI10P X264-TROLLUHD", quality.WEBDL_2160P),
            ("JUST ADD MAGIC S01E01.2160P AMZN WEBRIP DD2.0 X264-TROLLUHD", quality.WEBDL_2160P),
            ("The.Man.In.The.High.Castle.S01E01.2160p.AMZN.WEBRip.DD2.0.Hi10p.X264-TrollUHD", quality.WEBDL_2160P),
            ("The Man In the High Castle S01E01 2160p AMZN WEBRip DD2.0 Hi10P x264-TrollUHD", quality.WEBDL_2160P),
            ("The.Nightly.Show.2016.03.14.2160p.WEB.x264-spamTV", quality.WEBDL_2160P),
            ("The.Nightly.Show.2016.03.14.2160p.WEB.h264-spamTV", quality.WEBDL_2160P),
            ("The.Nightly.Show.2016.03.14.2160p.WEB.PROPER.h264-spamTV", quality.WEBDL_2160P),
            ("House.of.Cards.US.s05e13.4K.UHD.WEB.DL", quality.WEBDL_2160P),
            ("House.of.Cards.US.s05e13.UHD.4K.WEB.DL", quality.WEBDL_2160P),

            # bluray720
            ("WEEDS.S03E01-06.DUAL.Bluray.AC3.-HELLYWOOD.avi", quality.BLURAY_720P),
            ("Chuck - S01E03 - Come Fly With Me - 720p BluRay.mkv", quality.BLURAY_720P),
            ("The Big Bang Theory.S03E01.The Electric Can Opener Fluctuation.m2ts", quality.BLURAY_720P),
            ("Revolution.S01E02.Chained.Heat.[Bluray720p].mkv", quality.BLURAY_720P),
            ("[FFF] DATE A LIVE - 01 [BD][720p-AAC][0601BED4]", quality.BLURAY_720P),
            ("[coldhell] Pupa v3 [BD720p][03192D4C]", quality.BLURAY_720P),
            ("[RandomRemux] Nobunagun - 01 [720p BD][043EA407].mkv", quality.BLURAY_720P),
            ("[Kaylith] Isshuukan Friends Specials - 01 [BD 720p AAC][B7EEE164].mkv", quality.BLURAY_720P),
            ("WEEDS.S03E01-06.DUAL.Blu-ray.AC3.-HELLYWOOD.avi", quality.BLURAY_720P),
            ("WEEDS.S03E01-06.DUAL.720p.Blu-ray.AC3.-HELLYWOOD.avi", quality.BLURAY_720P),
            ("[Elysium]Lucky.Star.01(BD.720p.AAC.DA)[0BB96AD8].mkv", quality.BLURAY_720P),
            ("Battlestar.Galactica.S01E01.33.720p.HDDVD.x264-SiNNERS.mkv", quality.BLURAY_720P),
            ("The.Expanse.S01E07.RERIP.720p.BluRay.x264-DEMAND", quality.BLURAY_720P),
            ("Sans.Laisser.De.Traces.FRENCH.720p.BluRay.x264-FHD", quality.BLURAY_720P),

            # bluray1080
            ("Chuck - S01E03 - Come Fly With Me - 1080p BluRay.mkv", quality.BLURAY_1080P),
            ("Sons.Of.Anarchy.S02E13.1080p.BluRay.x264-AVCDVD", quality.BLURAY_1080P),
            ("Revolution.S01E02.Chained.Heat.[Bluray1080p].mkv", quality.BLURAY_1080P),
            ("[FFF] Namiuchigiwa no Muromi-san - 10 [BD][1080p-FLAC][0C4091AF]", quality.BLURAY_1080P),
            ("[coldhell] Pupa v2 [BD1080p][5A45EABE].mkv", quality.BLURAY_1080P),
            ("[Kaylith] Isshuukan Friends Specials - 01 [BD 1080p FLAC][429FD8C7].mkv", quality.BLURAY_1080P),
            ("[Zurako] Log Horizon - 01 - The Apocalypse (BD 1080p AAC) [7AE12174].mkv", quality.BLURAY_1080P),
            ("WEEDS.S03E01-06.DUAL.1080p.Blu-ray.AC3.-HELLYWOOD.avi", quality.BLURAY_1080P),
            # TODO - the "source_regex" word boundaries don't work with the surrounding underscores,.ie "_Blu-ray_"
            #("[Coalgirls]_Durarara!!_01_(1920x1080_Blu-ray_FLAC)_[8370CB8F].mkv", quality.BLURAY_1080P),
            ("Planet.Earth.S01E11.Ocean.Deep.1080p.HD-DVD.DD.VC1-TRB", quality.BLURAY_1080P),
            ("Spirited Away(2001) Bluray FHD Hi10P.mkv", quality.BLURAY_1080P),

            # bluray2160
            ("House.of.Cards.US.s05e13.4K.UHD.Bluray", quality.BLURAY_2160P),
            ("House.of.Cards.US.s05e13.UHD.4K.Bluray", quality.BLURAY_2160P),
            ("[DameDesuYo] Backlog Bundle - Part 1 (BD 4K 8bit FLAC)", quality.BLURAY_2160P),

            # rawhd
            ("POI S02E11 1080i HDTV DD5.1 MPEG2-TrollHD", quality.RAW_HD),
            ("How I Met Your Mother S01E18 Nothing Good Happens After 2 A.M. 720p HDTV DD5.1 MPEG2-TrollHD", quality.RAW_HD),
            ("The Voice S01E11 The Finals 1080i HDTV DD5.1 MPEG2-TrollHD", quality.RAW_HD),
            ("Californication.S07E11.1080i.HDTV.DD5.1.MPEG2-NTb.ts", quality.RAW_HD),
            ("Game of Thrones S04E10 1080i HDTV MPEG2 DD5.1-CtrlHD.ts", quality.RAW_HD),
            ("VICE.S02E05.1080i.HDTV.DD2.0.MPEG2-NTb.ts", quality.RAW_HD),
            ("Show - S03E01 - Episode Title Raw-HD.ts", quality.RAW_HD),
            ("Saturday.Night.Live.Vintage.S10E09.Eddie.Murphy.The.Honeydrippers.1080i.UPSCALE.HDTV.DD5.1.MPEG2-zebra", quality.RAW_HD),
            ("The.Colbert.Report.2011-08-04.1080i.HDTV.MPEG-2-CtrlHD", quality.RAW_HD),

            # unknown
            ("Sonny.With.a.Chance.S02E15", quality.UNKNOWN),
            ("Law & Order: Special Victims Unit - 11x11 - Quickie", quality.UNKNOWN),
            ("Series.Title.S01E01.webm", quality.UNKNOWN),
            ("Droned.S01E01.The.Web.MT-dd", quality.UNKNOWN),
        ]

    def test_quality(self):
        for name, expected_quality in self.quality_tests:
            parser = ParserBase(name)
            parser_quality = parser.parse_quality(name)
            self.assertTrue(parser_quality == expected_quality, '{} : {} != {}'.format(name, parser_quality, expected_quality))
