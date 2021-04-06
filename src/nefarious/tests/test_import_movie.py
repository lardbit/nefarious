import os

from django.contrib.auth.models import User
from django.test import TestCase
from nefarious.models import NefariousSettings, WatchMovie
from nefarious.importer.movie import MovieImporter
from nefarious.tmdb import get_tmdb_client


class MovieImportTest(TestCase):
    movie_tests = []

    def setUp(self):
        self.movie_tests = [
            # file path, title
            ('2 Guns (2013)/2.Guns.2013.720p.BluRay.x264.YIFY.mp4', "2 Guns"),
            ('2 Guns (2013)/2.Guns.2013.720p.BluRay.x264.YIFY.txt', False),
            ('Kingsman The Secret Service (2014) [1080p]/Kingsman.The.Secret.Service.2014.1080p.BluRay.x264.YIFY.mp4', 'Kingsman: The Secret Service'),
            ('Holmes & Watson (2018) 720p WEB-DL x264 Ganool.mkv', 'Holmes & Watson'),
            ('The.greatest.showman.2017.1080p-dual-lat-cinecalidad.to.mp4', 'The Greatest Showman'),
            ('fake movie 2013.mkv', False),
            ('fake movie.mkv', False),
        ]

    def test_movie(self):
        # populate some required data
        nefarious_settings = NefariousSettings()
        # required tmdb config data for saving models
        nefarious_settings.tmdb_configuration = {
            'images': {
                'secure_base_url': 'https://image.tmdb.org/t/p/',
            },
        }
        tmdb_client = get_tmdb_client(nefarious_settings)
        # use the first super user account to assign media
        user = User.objects.create_superuser('test', 'test@test.com', 'test')

        # import
        importer = MovieImporter(
            nefarious_settings=nefarious_settings,
            root_path='/test-download',
            tmdb_client=tmdb_client,
            user=user,
        )
        for test_result in self.movie_tests:
            # prepend '/movie' to the test path
            test_path = os.path.join('/movie', test_result[0])
            import_result = importer.ingest_path(test_path)
            if test_result[1] is False or import_result is False:
                self.assertEqual(test_result[1], import_result, '{} != {}'.format(test_result[1], import_result))
            else:
                watch_movie = WatchMovie(name=test_result[1])
                self.assertTrue(
                    watch_movie.name == import_result.name,
                    '{} != {}'.format(watch_movie.name, import_result.name))
