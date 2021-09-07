from django.utils import timezone
from django.utils.dateparse import parse_date

from nefarious.models import WatchMovie
from nefarious.parsers.movie import MovieParser
from nefarious.importer.base import ImporterBase


class MovieImporter(ImporterBase):
    media_class = WatchMovie

    def _get_parser(self, file_name):
        return MovieParser(file_name)

    def _get_tmdb_search_results(self, title):
        return self.tmdb_search.movie(query=title, language=self.nefarious_settings.language)

    def _is_result_match_title(self, parser, tmdb_result, title):
        return parser.normalize_media_title(tmdb_result.get('title')) == title

    def _handle_match(self, parser, tmdb_result, title, file_path):
        poster_path = self.nefarious_settings.get_tmdb_poster_url(tmdb_result['poster_path']) if tmdb_result['poster_path'] else ''
        watch_movie, _ = WatchMovie.objects.update_or_create(
            tmdb_movie_id=tmdb_result['id'],
            defaults=dict(
                user=self.user,
                name=tmdb_result['title'],
                poster_image_url=poster_path,
                download_path=file_path,
                collected=True,
                collected_date=timezone.utc.localize(timezone.datetime.utcnow()),
                release_date=parse_date(tmdb_result.get('release_date', '')),
                last_attempt_date=timezone.utc.localize(timezone.datetime.utcnow()),
            ),
        )
        return watch_movie
