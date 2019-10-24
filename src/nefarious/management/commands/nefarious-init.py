from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from nefarious.models import NefariousSettings
from nefarious.tmdb import get_tmdb_client


class Command(BaseCommand):
    help = 'Initialize Nefarious'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('email', type=str)
        parser.add_argument('password', type=str)

    def handle(self, *args, **options):

        # create superuser if they don't already exist
        existing_user = User.objects.filter(username=options['username'])
        if not existing_user.exists():
            User.objects.create_superuser(options['username'], options['email'], options['password'])
            self.stdout.write(self.style.SUCCESS('Successfully created superuser {}:{} {}'.format(
                options['username'], options['password'], options['email'])))

        # create settings if they don't already exist
        nefarious_settings, _ = NefariousSettings.objects.get_or_create()

        # populate tmdb configuration if necessary
        if not nefarious_settings.tmdb_configuration or not nefarious_settings.tmdb_languages:
            tmdb_client = get_tmdb_client(nefarious_settings)
            configuration = tmdb_client.Configuration()
            nefarious_settings.tmdb_configuration = configuration.info()
            nefarious_settings.tmdb_languages = configuration.languages()
            nefarious_settings.save()
