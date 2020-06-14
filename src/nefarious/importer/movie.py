import os
import logging

from django.core.cache import cache
from django.utils import timezone
from requests import HTTPError

from nefarious.models import WatchMovie
from nefarious.parsers.movie import MovieParser
from nefarious.quality import video_extensions
from nefarious.importer.base import ImporterBase


class MovieImporter(ImporterBase):

    def ingest_path(self, file_path):
        file_name = os.path.basename(file_path)

        parser = MovieParser(file_name)

        # match
        if parser.match:
            file_extension_match = parser.file_extension_regex.search(file_name)
            if file_extension_match:
                title = parser.match['title']
                if not title:
                    logging.warning('[NO_MATCH_TITLE] Could not match file without title "{}"'.format(file_path))
                    return False
                file_extension = file_extension_match.group()
                if file_extension in video_extensions():
                    if WatchMovie.objects.filter(download_path=file_path).exists():
                        logging.info('[SKIP] skipping already-processed file "{}"'.format(file_path))
                        return False
                    # get or set tmdb search results for this title in the cache
                    results = cache.get(title)
                    if not results:
                        try:
                            results = self.tmdb_search.movie(query=title, language=self.nefarious_settings.language)
                        except HTTPError:
                            logging.error('[ERROR_TMDB] tmdb search exception for title {} on file "{}"'.format(title, file_path))
                            return False
                        cache.set(title, results, 60 * 60)
                    # loop over results for the exact match
                    for result in results['results']:
                        poster_path = self.nefarious_settings.get_tmdb_poster_url(result['poster_path']) if result['poster_path'] else ''
                        # normalize titles and see if they match
                        if parser.normalize_media_title(result['title']) == title:
                            watch_movie, _ = WatchMovie.objects.get_or_create(
                                tmdb_movie_id=result['id'],
                                defaults=dict(
                                    user=self.user,
                                    name=result['title'],
                                    poster_image_url=poster_path,
                                    download_path=file_path,
                                    collected=True,
                                    collected_date=timezone.utc.localize(timezone.datetime.utcnow()),
                                ),
                            )
                            logging.info('[MATCH] Saved episode "{}" from file "{}"'.format(watch_movie, file_path))
                            return watch_movie
                    else:  # for/else
                        logging.warning('[NO_MATCH_MEDIA] No media match for title "{}" and file "{}"'.format(title, file_path))
                else:
                    logging.warning('[NO_MATCH_VIDEO] No valid video file extension for file "{}"'.format(file_path))
            else:
                logging.warning('[NO_MATCH_EXTENSION] No file extension for file "{}"'.format(file_path))
        else:
            logging.info('[NO_MATCH_UNKNOWN] Unknown match for file "{}"'.format(file_path))
        return False
