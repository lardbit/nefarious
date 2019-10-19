from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from nefarious.models import NefariousSettings


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
        NefariousSettings.objects.get_or_create()
