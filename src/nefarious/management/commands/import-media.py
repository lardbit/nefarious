import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from nefarious.importer.movie import MovieImporter
from nefarious.importer.tv import TVImporter
from nefarious.tmdb import get_tmdb_client
from nefarious.models import NefariousSettings


class Command(BaseCommand):
    help = 'Import library'
    MEDIA_TYPE_MOVIE = 'movie'
    MEDIA_TYPE_TV = 'tv'
    MEDIA_TYPES = [MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV]

    def add_arguments(self, parser):
        parser.add_argument('media_type', type=str, choices=self.MEDIA_TYPES)

    def handle(self, *args, **options):
        nefarious_settings = NefariousSettings.get()
        download_path = settings.INTERNAL_DOWNLOAD_PATH
        tmdb_client = get_tmdb_client(nefarious_settings)
        # use the first super user account to assign media
        user = User.objects.filter(is_superuser=True).first()

        # validate
        if not download_path:
            raise CommandError('INTERNAL_DOWNLOAD_PATH environment variable is not defined')
        elif not os.path.exists(download_path):
            raise CommandError('Path "{}" does not exist'.format(download_path))

        # import
        if options['media_type'] == self.MEDIA_TYPE_TV:
            tv_path = os.path.join(download_path, nefarious_settings.transmission_tv_download_dir)
            importer = TVImporter(
                nefarious_settings=nefarious_settings,
                root_path=tv_path,
                tmdb_client=tmdb_client,
                user=user,
            )
            importer.ingest_root(tv_path)
        else:
            movie_path = os.path.join(download_path, nefarious_settings.transmission_movie_download_dir)
            importer = MovieImporter(
                nefarious_settings=nefarious_settings,
                root_path=movie_path,
                tmdb_client=tmdb_client,
                user=user,
            )
            importer.ingest_root(movie_path)


