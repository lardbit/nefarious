from django.core.management.base import BaseCommand
from nefarious.parsers.tv import TVParser


class Command(BaseCommand):
    help = 'Test TV Parsing'

    def add_arguments(self, parser):
        parser.add_argument('title', type=str)

    def handle(self, *args, **options):
        parser = TVParser(options['title'])
        print(parser.match)
