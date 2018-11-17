import tmdbsimple as tmdb
from nefarious.models import NefariousSettings


def get_tmdb_client(nefarious_settings: NefariousSettings):
    tmdb.API_KEY = nefarious_settings.tmdb_token
    return tmdb
