import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from requests import HTTPError

from nefarious.tmdb import get_tmdb_client
from nefarious.parsers.tv import TVParser
from nefarious.models import NefariousSettings, WatchTVEpisode, WatchTVShow
from nefarious.quality import video_extensions


class Command(BaseCommand):
    help = 'Import library'
    download_path = None
    nefarious_settings = None
    tmdb_client = None
    tmdb_search = None
    user = None
    INGEST_DEPTH_MAX = 3

    def handle(self, *args, **options):
        self.nefarious_settings = NefariousSettings.get()
        self.download_path = settings.DOWNLOAD_PATH
        self.tmdb_client = get_tmdb_client(self.nefarious_settings)
        self.tmdb_search = self.tmdb_client.Search()
        self.user = User.objects.filter(is_superuser=True).first()  # use the first super user account to assign media

        # validate
        if not self.download_path:
            CommandError('DOWNLOAD_PATH is not defined')
        tv_path = os.path.join(self.download_path, self.nefarious_settings.transmission_tv_download_dir)
        if not os.path.exists(tv_path):
            CommandError('Path "{}" does not exist'.format(tv_path))

        for file_name in os.listdir(tv_path):
            self._ingest_path(tv_path, file_name)

    def _ingest_path(self, path, file_name):
        file_path = os.path.join(path, file_name)

        parser = TVParser(file_name)

        # match
        if parser.match:
            # file
            if os.path.isfile(file_path):
                file_extension_match = parser.file_extension_regex.search(file_name)
                if file_extension_match:
                    title = parser.match['title']
                    # no title found so it could be sub-directories like:
                    #   show/season 01/s01e01.mkv
                    #   show - season 01/s01e01.mkv
                    if not title:
                        if self._ingest_depth(file_path) > 1:

                            # append the top most parent folder as the title, i.e "show/season 01/s01e01.mkv" would become "show - s01e01.mkv"
                            file_path_split = file_path.split(os.sep)

                            # possible parent directories
                            parent_titles = [
                                # "show - season 01/s01e01.mkv" would define title as "show - season 01"
                                os.path.basename(os.sep.join(file_path_split[:-(self._ingest_depth(file_path) - 1)])),
                                # "show/season 01/s01e01.mkv" would define title as "show - s01e01.mkv"
                                '{} - {}'.format(
                                    os.path.basename(os.sep.join(file_path_split[:-(self._ingest_depth(file_path) - 1)])), file_name),
                            ]
                            for parent_title in parent_titles:
                                parent_parser = TVParser(parent_title)
                                # define the title and merge the parent and the file parser matches
                                if parent_parser.match and parent_parser.match['title']:
                                    title = parent_parser.match['title']
                                    parser.match.update(parent_parser.match)
                                    break
                            else:  # for/else
                                self.stderr.write(self.style.WARNING('[ERROR_NO_MATCH_TITLE] Could not match nested file "{}"'.format(file_path)))
                                return
                        else:
                            self.stderr.write(self.style.WARNING('[ERROR_NO_MATCH_TITLE] Could not match file without title "{}"'.format(file_path)))
                            return
                    file_extension = file_extension_match.group()
                    if file_extension in video_extensions():
                        if parser.is_single_episode():
                            if WatchTVEpisode.objects.filter(download_path=file_path).exists():
                                self.stderr.write(self.style.WARNING('[SKIP] skipping already-processed file "{}"'.format(file_path)))
                                return
                            # get or set tmdb search results for this title in the cache
                            results = cache.get(title)
                            if not results:
                                try:
                                    results = self.tmdb_search.tv(query=title, language=self.nefarious_settings.language)
                                except HTTPError:
                                    self.stderr.write(self.style.WARNING('[ERROR_TMDB] tmdb search exception for title {} on file "{}"'.format(title, file_path)))
                                    return
                                cache.set(title, results, 60 * 60)
                            # loop over results for the exact match
                            for result in results['results']:
                                poster_path = self.nefarious_settings.get_tmdb_poster_url(result['poster_path']) if result['poster_path'] else ''
                                # normalize titles and see if they match
                                if parser.normalize_media_title(result['name']) == title:
                                    season_number = parser.match['season'][0]
                                    episode_number = parser.match['episode'][0]
                                    watch_show, _ = WatchTVShow.objects.get_or_create(
                                        tmdb_show_id=result['id'],
                                        defaults=dict(
                                            user=self.user,
                                            name=result['name'],
                                            poster_image_url=poster_path,
                                        ),
                                    )
                                    episode_result = self.tmdb_client.TV_Episodes(result['id'], season_number, episode_number)
                                    try:
                                        episode_data = episode_result.info()
                                    except HTTPError:
                                        self.stderr.write(
                                            self.style.WARNING('[ERROR_TMDB] tmdb episode exception for title {} on file "{}"'.format(title, file_path)))
                                        return
                                    watch_episode, _ = WatchTVEpisode.objects.update_or_create(
                                        tmdb_episode_id=episode_data['id'],
                                        defaults=dict(
                                            user=self.user,
                                            watch_tv_show=watch_show,
                                            season_number=season_number,
                                            episode_number=episode_number,
                                            download_path=file_path,
                                            collected=True,
                                            collected_date=timezone.utc.localize(timezone.datetime.utcnow()),
                                        ),
                                    )
                                    self.stdout.write(
                                        self.style.SUCCESS('[MATCH] Saved episode "{}" from file "{}"'.format(watch_episode, file_path)))
                                    break
                            else:  # for/else
                                self.stderr.write(self.style.ERROR('[ERROR_NO_MATCH_MEDIA] No media match for title "{}" and file "{}"'.format(title, file_path)))
                        else:
                            self.stderr.write(self.style.WARNING('[ERROR_NO_MATCH_SINGLE_EPISODE] No single episode title match for title "{}" and file "{}"'.format(title, file_path)))
                    else:
                        self.stderr.write(self.style.WARNING('[ERROR_NO_MATCH_VIDEO] No valid video file extension for file "{}"'.format(file_path)))
                else:
                    self.stderr.write(self.style.WARNING('[ERROR_NO_MATCH_EXTENSION] No file extension for file "{}"'.format(file_path)))

            # directory
            elif self._is_dir(file_path) and self._ingest_depth(file_path) < self.INGEST_DEPTH_MAX:
                for sub_path in os.listdir(file_path):
                    self._ingest_path(file_path, sub_path)
        # no match so dig deeper
        elif self._is_dir(file_path) and self._ingest_depth(file_path) < self.INGEST_DEPTH_MAX:
            for sub_path in os.listdir(file_path):
                self._ingest_path(file_path, sub_path)
        else:
            self.stderr.write(self.style.NOTICE('[ERROR_NO_MATCH_UNKNOWN] Unknown match for file "{}"'.format(file_path)))

    def _is_dir(self, path) -> bool:
        # is a directory and NOT a symlink
        return os.path.isdir(path) and not os.path.islink(path)

    def _ingest_depth(self, path) -> int:
        root_depth = len(os.path.normpath(self.download_path).split(os.sep))
        path_depth = len(os.path.normpath(path).split(os.sep))
        # subtract 1 to account for the movies and tv subdirectories, i.e /download/path/tv & /download/path/movies
        return path_depth - root_depth - 1
