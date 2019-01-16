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
        nefarious_settings = NefariousSettings.get()
        params = {
            'apikey': nefarious_settings.jackett_token,
            'Query': query,
        }

        params.update(self._categories_params(media_type))

        res = requests.get(get_jackett_search_url(nefarious_settings), params, timeout=120)

        if res.ok:
            response = res.json()
            self.results = response['Results']
        else:
            self.ok = False
            self.error_content = res.content

    def _categories_params(self, media_type: str) -> dict:
        cat_movies = [2000, 2010, 2030, 2040, 2050, 2060, 2070]
        cat_tv = [5000, 5010, 5020, 5030, 5040, 5060, 5070, 5080]
        if media_type == MEDIA_TYPE_MOVIE:
            categories = cat_movies
        else:
            categories = cat_tv
        return dict(('Category[{}]'.format(idx), cat) for idx, cat in enumerate(categories))


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
