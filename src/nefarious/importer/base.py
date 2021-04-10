import os

from django.core.cache import cache
from requests import HTTPError

from nefarious.quality import video_extensions
from nefarious.utils import logger_background


class ImporterBase:
    root_path = None
    nefarious_settings = None
    tmdb_client = None
    tmdb_search = None
    user = None
    media_class = None

    def __init__(self, nefarious_settings, root_path, tmdb_client, user):
        self.nefarious_settings = nefarious_settings
        self.root_path = root_path
        self.tmdb_client = tmdb_client
        self.tmdb_search = tmdb_client.Search()
        self.user = user

    def ingest_root(self, path):
        scanned = 0
        logger_background.info('Scanning {}'.format(path))
        for root, dirs, files in os.walk(path):
            scanned += len(files)
            for file in files:
                self.ingest_path(os.path.join(root, file))
        logger_background.info('Scanned {} files'.format(scanned))

    def _handle_match(self, parser, tmdb_result, title, file_path):
        raise NotImplementedError

    def _is_result_match_title(self, parser, tmdb_result, title):
        raise NotImplementedError

    def _handle_missing_title(self, parser, path) -> tuple:
        return None, None

    def _get_parser(self, file_name):
        raise NotImplementedError

    def _is_parser_exact_match(self, parser) -> bool:
        return True

    def _get_tmdb_search_results(self, title):
        raise NotImplementedError

    def ingest_path(self, file_path):
        file_name = os.path.basename(file_path)

        parser = self._get_parser(file_name)

        # match
        if parser.match:
            file_extension_match = parser.file_extension_regex.search(file_name)
            if file_extension_match:
                # skip sample files
                if parser.sample_file_regex.search(file_name):
                    logger_background.warning('[NO_MATCH_SAMPLE] Not matching sample file "{}"'.format(file_path))
                    return False
                title = parser.match['title']
                if not title:
                    new_title, parser_match = self._handle_missing_title(parser, file_path)
                    if new_title:
                        title = new_title
                        parser.match.update(parser_match)
                    else:
                        logger_background.warning('[NO_MATCH_TITLE] Could not match file without title "{}"'.format(file_path))
                        return False
                file_extension = file_extension_match.group()
                if file_extension in video_extensions():
                    if self._is_parser_exact_match(parser):
                        if self.media_class.objects.filter(download_path=file_path).exists():
                            logger_background.info('[SKIP] skipping already-processed file "{}"'.format(file_path))
                            return False
                        # get or set tmdb search results for this title in the cache
                        tmdb_results = cache.get(title)
                        if not tmdb_results:
                            try:
                                tmdb_results = self._get_tmdb_search_results(title)
                            except HTTPError:
                                logger_background.error('[ERROR_TMDB] tmdb search exception for title {} on file "{}"'.format(title, file_path))
                                return False
                            cache.set(title, tmdb_results, 60 * 60)
                        # loop over results for the exact match
                        for tmdb_result in tmdb_results['results']:
                            # normalize titles and see if they match
                            if self._is_result_match_title(parser, tmdb_result, title):
                                watch_media = self._handle_match(parser, tmdb_result, title, file_path)
                                if watch_media:
                                    logger_background.info('[MATCH] Saved media "{}" from file "{}"'.format(watch_media, file_path))
                                    return watch_media
                        else:  # for/else
                            logger_background.warning('[NO_MATCH_MEDIA] No media match for title "{}" and file "{}"'.format(title, file_path))
                    else:
                        logger_background.warning('[NO_MATCH_EXACT] No exact title match for title "{}" and file "{}"'.format(title, file_path))
                else:
                    logger_background.warning('[NO_MATCH_VIDEO] No valid video file extension for file "{}"'.format(file_path))
            else:
                logger_background.warning('[NO_MATCH_EXTENSION] No file extension for file "{}"'.format(file_path))
        else:
            logger_background.info('[NO_MATCH_UNKNOWN] Unknown match for file "{}"'.format(file_path))
        return False

    def _ingest_depth(self, path) -> int:
        root_depth = len(os.path.normpath(self.root_path).split(os.sep))
        path_depth = len(os.path.normpath(path).split(os.sep))
        # subtract 1 to account for the movies and tv subdirectories, i.e /download/path/tv & /download/path/movies
        return path_depth - root_depth - 1
