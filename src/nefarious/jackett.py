from nefarious.models import NefariousSettings


def get_jackett_search_url(nefarious_settings: NefariousSettings):
    return 'http://{}:{}/api/v2.0/indexers/all/results'.format(
        nefarious_settings.jackett_host, nefarious_settings.jackett_port)
