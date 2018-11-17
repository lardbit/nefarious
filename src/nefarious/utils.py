import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import requests
from urllib.parse import urlparse
from transmissionrpc import TransmissionError
from nefarious.models import NefariousSettings
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client


def is_magnet_url(url: str) -> bool:
    return url.startswith('magnet:')


def swap_jackett_host(url: str, nefarious_settings: NefariousSettings) -> str:
    parsed = urlparse(url)
    return '{}://{}:{}{}?{}'.format(
        parsed.scheme, nefarious_settings.jackett_host, nefarious_settings.jackett_port,
        parsed.path, parsed.query,
    )


def trace_torrent_url(url: str) -> str:

    if is_magnet_url(url):
        return url

    # validate torrent file response
    response = requests.get(url, allow_redirects=False, timeout=30)
    if not response.ok:
        raise Exception(response.content)
    # redirected to a magnet link so use that instead
    elif response.is_redirect and is_magnet_url(response.headers['Location']):
        return response.headers['Location']

    return url


def get_best_torrent_result(results: list, nefarious_settings: NefariousSettings):
    best_result = None
    valid_search_results = []

    for result in results:

        # try and obtain the torrent url (it can redirect to a magnet url)
        try:
            # add a new key to our result object with the traced torrent url
            result['torrent_url'] = result['MagnetUri'] or trace_torrent_url(
                swap_jackett_host(result['Link'], nefarious_settings))
        except Exception as e:
            logging.info('Exception tracing torrent url: {}'.format(e))
            continue

        # add torrent to valid search results
        logging.info('Valid Match: {} with {} Seeders'.format(result['Title'], result['Seeders']))
        valid_search_results.append(result)

    if valid_search_results:

        # find the torrent result with the highest weight (i.e seeds)
        best_result = valid_search_results[0]
        for result in valid_search_results:
            if result['Seeders'] > best_result['Seeders']:
                best_result = result

    else:
        logging.info('No valid best search result')

    return best_result


def verify_settings_tmdb(nefarious_settings: NefariousSettings):
    # verify tmdb configuration settings
    try:
        tmdb_client = get_tmdb_client(nefarious_settings)
        configuration = tmdb_client.Configuration()
        configuration.info()
    except Exception as e:
        logging.error(str(e))
        raise Exception('Could not fetch TMDB configuration')


def verify_settings_transmission(nefarious_settings: NefariousSettings):
    # verify transmission
    try:
        get_transmission_client(nefarious_settings)
    except TransmissionError:
        raise Exception('Could not connect to transmission')


def verify_settings_jackett(nefarious_settings: NefariousSettings):
    # verify jackett
    try:
        # make an unspecified query to the "all" indexer results endpoint and see if it's successful
        response = requests.get('http://{}:{}/api/v2.0/indexers/all/results'.format(
            nefarious_settings.jackett_host, nefarious_settings.jackett_port), params={'apikey': nefarious_settings.jackett_token}, timeout=60)
        response.raise_for_status()
    except Exception as e:
        logging.error(str(e))
        raise Exception('Could not connect to jackett')


def needs_tmdb_configuration(nefarious_settings: NefariousSettings):
    if not nefarious_settings.tmdb_configuration:
        return True
    elif not nefarious_settings.tmdb_configuration_date:
        return True
    elif (datetime.utcnow().replace(tzinfo=timezone.utc) - nefarious_settings.tmdb_configuration_date).days >= settings.TMDB_CONFIGURATION_STALE_DAYS:
        return True
    return False
