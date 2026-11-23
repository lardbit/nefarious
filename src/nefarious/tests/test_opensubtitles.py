from unittest.mock import Mock, patch, mock_open

from django.contrib.auth.models import User
from django.test import TestCase
from requests.exceptions import HTTPError

from nefarious import quality
from nefarious.models import NefariousSettings, QualityProfile, WatchTVEpisode, WatchTVShow
from nefarious.opensubtitles import OpenSubtitles


class OpenSubtitlesTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('admin', password='password', is_staff=True)
        quality_profile = QualityProfile.objects.create(name=quality.SDTV, quality=quality.SDTV)
        self.settings = NefariousSettings.objects.create(
            quality_profile_tv=quality_profile,
            quality_profile_movies=quality_profile,
            open_subtitles_user_token='expired-token',
        )
        self.show = WatchTVShow.objects.create(
            user=self.user, tmdb_show_id=2723, name='Samurai Jack', poster_image_url='http://example.com/poster.jpg')
        self.episode = WatchTVEpisode.objects.create(
            user=self.user, watch_tv_show=self.show, tmdb_episode_id=213540,
            season_number=1, episode_number=2, download_path='tv/Samurai Jack/S01E02.mkv')

    @staticmethod
    def search_result():
        return {
            'attributes': {
                'url': 'http://example.com/subtitles/123',
                'files': [{'file_id': 123}],
            },
        }

    @staticmethod
    def response(status_code, json_data=None, content=b''):
        response = Mock(status_code=status_code)
        response.ok = 200 <= status_code < 400
        response.json.return_value = json_data
        response.content = content
        if not response.ok:
            response.raise_for_status.side_effect = HTTPError('{} Client Error'.format(status_code))
        return response

    def download_result(self):
        return {'link': 'http://example.com/download/123', 'file_name': 'sub.srt'}

    @patch.object(OpenSubtitles, 'search', return_value=search_result())
    @patch.object(OpenSubtitles, 'auth', return_value=True)
    @patch('builtins.open', mock_open())
    def test_retries_once_after_401(self, auth, search):
        with patch.object(OpenSubtitles, '_request_download', side_effect=[
                self.response(401),
                self.response(200, json_data=self.download_result()),
        ]) as request_download, patch('nefarious.opensubtitles.requests.get',
                                       return_value=self.response(200, content=b'1\n00:00:01,000 --> 00:00:02,000\nhi\n')):

            OpenSubtitles().download(self.episode)

        self.assertEqual(2, request_download.call_count)
        self.assertEqual(1, auth.call_count)

    @patch.object(OpenSubtitles, 'search', return_value=search_result())
    @patch.object(OpenSubtitles, 'auth', return_value=True)
    def test_does_not_retry_on_other_error(self, auth, search):
        with patch.object(OpenSubtitles, '_request_download', return_value=self.response(500)):
            with self.assertRaises(HTTPError):
                OpenSubtitles().download(self.episode)

        self.assertEqual(0, auth.call_count)

    @patch.object(OpenSubtitles, 'search', return_value=search_result())
    @patch.object(OpenSubtitles, 'auth', return_value=False)
    def test_401_with_failed_reauth_raises(self, auth, search):
        with patch.object(OpenSubtitles, '_request_download', return_value=self.response(401)):
            with self.assertRaises(HTTPError):
                OpenSubtitles().download(self.episode)

        self.assertEqual(1, auth.call_count)

    @patch('nefarious.opensubtitles.requests.post')
    def test_request_download_uses_standard_bearer_header(self, requests_post):
        OpenSubtitles()._request_download(123)

        headers = requests_post.call_args.kwargs['headers']
        self.assertEqual('Bearer expired-token', headers['Authorization'])
        self.assertEqual(123, requests_post.call_args.kwargs['data']['file_id'])
