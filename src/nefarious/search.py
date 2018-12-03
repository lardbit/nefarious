import requests
from nefarious.jackett import get_jackett_search_url
from nefarious.models import NefariousSettings

MEDIA_TYPE_TV = 'tv'
MEDIA_TYPE_MOVIE = 'movie'


class SearchTorrents:
    results = None
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
            self.results = response
        else:
            self.ok = False
            self.error_content = res.content
