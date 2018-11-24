from nefarious.parsers.movie import MovieParser
from django.test import TestCase


class MovieMatch(TestCase):
    movie_tests = []

    def setUp(self):
        # full season tests
        self.movie_tests = [
            ("The.Man.from.U.N.C.L.E.2015.1080p.BluRay.x264-SPARKS", "The Man from U.N.C.L.E."),
            ("1941.1979.EXTENDED.720p.BluRay.X264-AMIABLE", "1941"),
            ("MY MOVIE (2016) [R][Action, Horror][720p.WEB-DL.AVC.8Bit.6ch.AC3].mkv", "MY MOVIE"),
            ("R.I.P.D.2013.720p.BluRay.x264-SPARKS", "R.I.P.D."),
            ("V.H.S.2.2013.LIMITED.720p.BluRay.x264-GECKOS", "V.H.S. 2"),
            ("This Is A Movie (1999) [IMDB #] <Genre, Genre, Genre> {ACTORS} !DIRECTOR +MORE_SILLY_STUFF_NO_ONE_NEEDS ?", "This Is A Movie"),
            ("We Are the Best!.2013.720p.H264.mkv", "We Are the Best!"),
            ("(500).Days.Of.Summer.(2009).DTS.1080p.BluRay.x264.NLsubs", "(500) Days Of Summer"),
            ("To.Live.and.Die.in.L.A.1985.1080p.BluRay", "To Live and Die in L.A."),
            ("A.I.Artificial.Intelligence.(2001)", "A.I. Artificial Intelligence"),
            ("A.Movie.Name.(1998)", "A Movie Name"),
            ("Thor: The Dark World 2013", "Thor The Dark World"),
            ("Resident.Evil.The.Final.Chapter.2016", "Resident Evil The Final Chapter"),
            ("Der.Soldat.James.German.Bluray.FuckYou.Pso.Why.cant.you.follow.scene.rules.1998", "Der Soldat James"),
            ("Passengers.German.DL.AC3.Dubbed..BluRay.x264-PsO", "Passengers"),
            ("Valana la Legende FRENCH BluRay 720p 2016 kjhlj", "Valana la Legende"),
            ("Valana la Legende TRUEFRENCH BluRay 720p 2016 kjhlj", "Valana la Legende"),
            ("Mission Impossible: Rogue Nation (2015)�[XviD - Ita Ac3 - SoftSub Ita]azione, spionaggio, thriller *Prima Visione* Team mulnic Tom Cruise", "Mission Impossible Rogue Nation"),
            ("Scary.Movie.2000.FRENCH..BluRay.-AiRLiNE", "Scary Movie"),
            ("My Movie 1999 German Bluray", "My Movie"),
        ]

    def test_movie(self):
        for name, title in self.movie_tests:
            parser = MovieParser(name)
            self.assertTrue(parser.is_match(title), '{} ({})'.format(name, parser.match))
