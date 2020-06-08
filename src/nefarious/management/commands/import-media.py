import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

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
                extension_match = parser.file_extension_regex.search(file_name)
                if extension_match:
                    title = parser.match['title']
                    extension = extension_match.group()
                    if extension in video_extensions():
                        if parser.is_single_episode():
                            # get or set tmdb search results for this title in the cache
                            results = cache.get(title)
                            if not results:
                                results = self.tmdb_search.tv(query=title, language=self.nefarious_settings.language)
                                cache.set(title, results, 60 * 60)
                            # loop over results for the exact match
                            for result in results['results']:
                                # normalize titles and see if they match
                                if parser.normalize_media_title(result['name']) == title:
                                    season_number = parser.match['season'][0]
                                    episode_number = parser.match['episode'][0]
                                    watch_show, _ = WatchTVShow.objects.get_or_create(
                                        tmdb_show_id=result['id'],
                                        defaults=dict(
                                            user=self.user,
                                            name=result['name'],
                                            poster_image_url=self.nefarious_settings.get_tmdb_poster_url(result['poster_path']),
                                        ),
                                    )
                                    episode_result = self.tmdb_client.TV_Episodes(result['id'], season_number, episode_number)
                                    episode_data = episode_result.info()
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
                                        self.style.SUCCESS('Matched episode "{}" with file "{}"'.format(watch_episode, file_name)))
                                    break
                            else:
                                self.stderr.write(self.style.ERROR('No media match for file "{}" and title "{}"'.format(file_name, title)))
                        else:
                            self.stderr.write(self.style.WARNING('No single episode title match for "{}"'.format(file_name)))
                    else:
                        self.stderr.write(self.style.WARNING('No valid video file extension for "{}"'.format(file_name)))
                else:
                    self.stderr.write(self.style.WARNING('No file extension for "{}"'.format(file_name)))

            # directory
            elif self._is_dir(file_path) and self._ingest_depth(file_path) <= self.INGEST_DEPTH_MAX:
                for sub_path in os.listdir(file_path):
                    self._ingest_path(file_path, sub_path)
        # no match so dig deeper
        elif self._is_dir(file_path) and self._ingest_depth(file_path) <= self.INGEST_DEPTH_MAX:
            for sub_path in os.listdir(file_path):
                self._ingest_path(file_path, sub_path)
        else:
            self.stderr.write(self.style.NOTICE('Unknown file "{}"'.format(file_path)))

    def _is_dir(self, path) -> bool:
        # is a directory and NOT a symlink
        return os.path.isdir(path) and not os.path.islink(path)

    def _ingest_depth(self, path) -> int:
        root_depth = len(os.path.normpath(self.download_path).split(os.sep))
        path_depth = len(os.path.normpath(path).split(os.sep))
        # subtract 1 to account for the movies and tv subdirectories, i.e /download/path/tv & /download/path/movies
        return path_depth - root_depth - 1
