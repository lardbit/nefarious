from nefarious.models import NefariousSettings


def get_jackett_search_url(nefarious_settings: NefariousSettings):
    return "http://{}:{}/api/v2.0/indexers/{}/results".format(
        nefarious_settings.jackett_host,
        nefarious_settings.jackett_port,
        # https://github.com/Jackett/Jackett#filter-indexers
        nefarious_settings.jackett_filter_index or 'all',
    )
