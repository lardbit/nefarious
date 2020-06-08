import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from nefarious.parsers.tv import TVParser
from nefarious.models import NefariousSettings
from nefarious.quality import video_extensions


class Command(BaseCommand):
    help = 'Import library'
    download_path = None
    INGEST_DEPTH_MAX = 3

    def handle(self, *args, **options):
        nefarious_settings = NefariousSettings.get()
        self.download_path = settings.DOWNLOAD_PATH

        self.stdout.write('Download path: {}'.format(self.download_path))

        # validate
        if not self.download_path:
            CommandError('DOWNLOAD_PATH is not defined')
        top_level_path = os.path.join(self.download_path, nefarious_settings.transmission_tv_download_dir)
        if not os.path.exists(top_level_path):
            CommandError('{} does not exist'.format(top_level_path))

        for file_name in os.listdir(top_level_path):
            self._ingest_path(top_level_path, file_name)

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
                            self.stdout.write(self.style.SUCCESS('Single Episode: {} for {}'.format(title, file_name)))
            # directory
            elif self._is_dir(file_path) and self._ingest_depth(file_path) <= self.INGEST_DEPTH_MAX:
                for sub_path in os.listdir(file_path):
                    self._ingest_path(file_path, sub_path)
        # no match so dig deeper
        elif self._is_dir(file_path) and self._ingest_depth(file_path) <= self.INGEST_DEPTH_MAX:
            for sub_path in os.listdir(file_path):
                self._ingest_path(file_path, sub_path)
        else:
            self.stdout.write(self.style.WARNING('No match for {}'.format(file_path)))

    def _is_dir(self, path) -> bool:
        return os.path.isdir(path) and not os.path.islink(path)

    def _ingest_depth(self, path) -> int:
        root_depth = len(os.path.normpath(self.download_path).split(os.sep))
        path_depth = len(os.path.normpath(path).split(os.sep))
        return path_depth - root_depth

