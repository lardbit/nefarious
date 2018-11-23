from django.core.management.base import BaseCommand
from nefarious.parsers.movie import MovieParser


class Command(BaseCommand):
    help = 'Test Movie Parsing'

    def add_arguments(self, parser):
        parser.add_argument('title', type=str)

    def handle(self, *args, **options):
        parser = MovieParser(options['title'])
        print(parser.match)
