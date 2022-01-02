from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from nefarious.models import NefariousSettings
from nefarious.tmdb import get_tmdb_client


class Command(BaseCommand):
    help = 'Initialize Nefarious'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True)
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)
        parser.add_argument('--transmission_user', type=str, required=True)
        parser.add_argument('--transmission_pass', type=str, required=True)

    def handle(self, *args, **options):

        # create superuser if they don't already exist
        existing_user = User.objects.filter(username=options['username'])
        if not existing_user.exists():
            User.objects.create_superuser(options['username'], options['email'], options['password'])
            self.stdout.write(self.style.SUCCESS('Successfully created superuser {}:{} {}'.format(
                options['username'], options['password'], options['email'])))

        # create settings if they don't already exist
        nefarious_settings, was_created = NefariousSettings.objects.get_or_create(
            defaults={
                # set transmission user/pass
                'transmission_user': options['transmission_user'],
                'transmission_pass': options['transmission_pass'],
            }
        )

        # populate tmdb configuration if settings were just created or tmdb conf absent
        if was_created or not all([nefarious_settings.tmdb_configuration, nefarious_settings.tmdb_languages]):
            tmdb_client = get_tmdb_client(nefarious_settings)
            configuration = tmdb_client.Configuration()
            nefarious_settings.tmdb_configuration = configuration.info()
            nefarious_settings.tmdb_languages = configuration.languages()
            nefarious_settings.save()
