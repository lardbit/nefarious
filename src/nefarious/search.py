import requests
from nefarious.jackett import get_jackett_search_url
from nefarious.models import NefariousSettings
from typing import List

MEDIA_TYPE_TV = 'tv'
MEDIA_TYPE_MOVIE = 'movie'


class SearchTorrents:
    results: list = None
    ok = True
    error_content = None

    def __init__(self, media_type: str, query: str):
        assert media_type in [MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE]
        nefarious_settings = NefariousSettings.singleton()
        category = 2000 if media_type == MEDIA_TYPE_MOVIE else 5000
        params = {
            'apikey': nefarious_settings.jackett_token,
            'Query': query,
            'Category[0]': category,
        }

        res = requests.get(get_jackett_search_url(nefarious_settings), params, timeout=120)

        if res.ok:
            response = res.json()
            self.results = response['Results']
        else:
            self.ok = False
            self.error_content = res.content


class SearchTorrentsCombined:
    results = []
    ok = True
    error_content = ''

    def __init__(self, search_torrents: List[SearchTorrents]):
        self.ok = any([search.ok for search in search_torrents])
        for search in search_torrents:
            if search.ok:
                self.results += search.results
            else:
                self.error_content += '\n{}'.format(search.error_content)
