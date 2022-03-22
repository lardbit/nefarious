import os

from django.utils import timezone
from django.utils.dateparse import parse_date
from requests import HTTPError

from nefarious.models import WatchTVEpisode, WatchTVShow
from nefarious.parsers.tv import TVParser
from nefarious.importer.base import ImporterBase
from nefarious.utils import logger_background


class TVImporter(ImporterBase):
    media_class = WatchTVEpisode
    INGEST_DEPTH_MAX = 3

    def _get_tmdb_search_results(self, title):
        return self.tmdb_search.tv(query=title, language=self.nefarious_settings.language)

    def _get_parser(self, file_name):
        return TVParser(file_name)

    def _is_result_match_title(self, parser, tmdb_result, title):
        if not tmdb_result.get('name'):
            return False
        return parser.normalize_media_title(tmdb_result['name']) == title and parser.is_single_episode()

    def _handle_missing_title(self, parser, file_path) -> tuple:
        file_name = os.path.basename(file_path)

        if self._ingest_depth(file_path) > 0:

            # append the top most parent folder as the title, i.e "show/season 01/s01e01.mkv" would become "show - s01e01.mkv"
            file_path_split = file_path.split(os.sep)

            # possible parent directories
            parent_titles = [
                # "show - season 01/s01e01.mkv" would define title as "show - season 01"
                os.path.basename(os.sep.join(file_path_split[:-(self._ingest_depth(file_path))])),
                # "show/season 01/s01e01.mkv" would define title as "show - s01e01.mkv"
                '{} - {}'.format(
                    os.path.basename(os.sep.join(file_path_split[:-(self._ingest_depth(file_path))])), file_name),
            ]
            for parent_title in parent_titles:
                parent_parser = TVParser(parent_title)
                # define the title and merge the parent and the file parser matches
                if parent_parser.match and parent_parser.match['title']:
                    title = parent_parser.match['title']
                    parser.match.update(parent_parser.match)
                    return title, parser.match
            else:  # for/else
                logger_background.warning('[NO_MATCH_TITLE] Could not match nested file "{}"'.format(file_path))
                return False, False
        else:
            logger_background.warning('[NO_MATCH_TITLE] Could not match file without title "{}"'.format(file_path))
            return False, False

    def _handle_match(self, parser, tmdb_result, title, file_path):
        poster_path = self.nefarious_settings.get_tmdb_poster_url(tmdb_result['poster_path']) if tmdb_result['poster_path'] else ''
        season_number = parser.match['season'][0]
        episode_number = parser.match['episode'][0]
        watch_show, _ = WatchTVShow.objects.update_or_create(
            tmdb_show_id=tmdb_result['id'],
            defaults=dict(
                user=self.user,
                name=tmdb_result['name'],
                poster_image_url=poster_path,
            ),
        )
        episode_result = self.tmdb_client.TV_Episodes(tmdb_result['id'], season_number, episode_number)
        try:
            episode_data = episode_result.info()
        except HTTPError:
            logger_background.error('[ERROR_TMDB] tmdb episode exception for title {} on file "{}"'.format(title, file_path))
            return False
        watch_episode, _ = WatchTVEpisode.objects.update_or_create(
            watch_tv_show=watch_show,
            season_number=season_number,
            episode_number=episode_number,
            defaults=dict(
                tmdb_episode_id=episode_data['id'],
                user=self.user,
                download_path=file_path,
                collected=True,
                collected_date=timezone.utc.localize(timezone.datetime.utcnow()),
                release_date=parse_date(episode_data.get('air_date', '')),
                last_attempt_date=timezone.utc.localize(timezone.datetime.utcnow()),
            ),
        )
        return watch_episode
