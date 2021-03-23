import os
import struct
import requests
from typing import Union
from nefarious.models import NefariousSettings, WatchMovie
from nefarious.parsers.base import ParserBase
from nefarious.utils import logger_background


class OpenSubtitles:
    API_URL_BASE = 'https://www.opensubtitles.com/api/v1'
    API_URL_AUTH = '{base}/login'.format(base=API_URL_BASE)
    API_URL_SEARCH = '{base}/subtitles'.format(base=API_URL_BASE)

    user_token: str = None
    error_message: str = None
    _response = None

    def __init__(self):
        self.nefarious_settings = NefariousSettings.get()

    def auth(self):
        self._response = requests.post(
            self.API_URL_AUTH,
            data={
                'username': self.nefarious_settings.open_subtitles_username,
                'password': self.nefarious_settings.open_subtitles_password,
            },
            headers={'Api-Key': self.nefarious_settings.open_subtitles_api_key},
            timeout=30,
        )
        if self._response.ok:
            try:
                data = self._response.json()
            except ValueError:
                self.error_message = 'auth did not return valid json'
                return False
            if 'token' not in data:
                self.error_message = 'token not found in response'
                return False
            # save user token
            self.user_token = data['token']
            self.nefarious_settings.open_subtitles_user_token = self.user_token
            self.nefarious_settings.save()
        else:
            self.error_message = 'Unable to authenticate with provided credentials'
        return self._response.ok

    def search(self, tmdb_id: int, path: str) -> Union[dict, bool]:
        media_hash = self.media_hash(path)
        self._response = requests.get(
            self.API_URL_SEARCH,
            params={
                'type': 'movie',  # TODO - handle TV
                'tmdb_id': tmdb_id,
                'moviehash': media_hash,
                'languages': self.nefarious_settings.language,
            },
            headers={'Api-Key': self.nefarious_settings.open_subtitles_api_key},
            timeout=30,
        )
        if not self._response.ok:
            self.error_message = 'An unknown error occurred searching for tmdb_id {} and media hash {}'.format(
                tmdb_id, media_hash,
            )
            return False

        # find best result
        data = self._response.json()
        if 'data' in data and len(data['data']) > 0:
            results = self._sort_results(data['data'])
            results = self._single_file_results(results)
            hash_matched_results = self._hash_match_results(results)
            # has direct hash matches
            if hash_matched_results:
                return hash_matched_results[0]
            # otherwise just return best match
            else:
                return results[0]
        else:
            self.error_message = 'No results found'
            return False

    def download(self, watch_media: WatchMovie):
        # TODO - handle TV vs Movie w/ tmdb_id
        # downloads the matching subtitle to the media's path

        # download subtitle
        result = self.search(watch_media.tmdb_movie_id, watch_media.download_path)
        response = requests.get(result['link'], timeout=30)
        response.raise_for_status()

        # define subtitle extension
        extension = '.srt'
        file_extension_match = ParserBase.file_extension_regex.search(result['file_name'])
        if file_extension_match:
            extension = file_extension_match.group().lower()

        # define subtitle download path
        subtitle_path = os.path.join(watch_media.download_path, '{}.{}'.format(watch_media, extension))

        logger_background.info('downloading subtitle {} to {}'.format(result['file_name'], subtitle_path))

        # save subtitle
        with open(subtitle_path, 'rb') as fh:
            fh.write(response.content)

    @staticmethod
    def _single_file_results(results: list):
        # only include results with a single subtitle file since
        # media apps like Plex only expect a single file
        # https://support.plex.tv/articles/200471133-adding-local-subtitles-to-your-media/
        results = [r for r in results if len(r.get('attributes', {}).get('files', [])) == 1]
        return results

    @staticmethod
    def _hash_match_results(results: list):
        # TODO - TV probably doesn't use "moviehash_match" param?
        results = [r for r in results if r.get('attributes', {}).get('moviehash_match')]
        return results

    @staticmethod
    def _sort_results(results: list):
        # sort by "points" desc
        results.sort(key=lambda x: x.get('attributes', {}).get('points', 0), reverse=True)
        return results

    @staticmethod
    def media_hash(path: str) -> str:
        """
        Media hash used for exact file matching in Open Subtitles
        https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
        """

        long_long_format = '<q'  # little-endian long long
        byte_size = struct.calcsize(long_long_format)

        f = open(path, "rb")

        filesize = os.path.getsize(path)
        hash_str = filesize

        if filesize < 65536 * 2:
            raise Exception('Hash size error')

        for x in range(int(65536 / byte_size)):
            buffer = f.read(byte_size)
            (l_value,) = struct.unpack(long_long_format, buffer)
            hash_str += l_value
            hash_str = hash_str & 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

        f.seek(max(0, filesize - 65536), 0)
        for x in range(int(65536 / byte_size)):
            buffer = f.read(byte_size)
            (l_value,) = struct.unpack(long_long_format, buffer)
            hash_str += l_value
            hash_str = hash_str & 0xFFFFFFFFFFFFFFFF

        f.close()
        returned_hash = "%016x" % hash_str

        return returned_hash
