import re
import os
import logging
import regex
import requests
from typing import List
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from transmissionrpc import TransmissionError

from nefarious.models import NefariousSettings, WatchMovie, WatchTVSeason, WatchTVEpisode, WatchMediaBase
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
    """
    A special "all" indexer is available at /api/v2.0/indexers/all/results/torznab/api. It will query all configured indexers and return the combined results.
    NOTE: /api/v2.0/indexers/all/results  will return json results vs torznab's xml response
    """
    try:
        # make an unspecified query to the "all" indexer results endpoint and see if it's successful
        response = requests.get('http://{}:{}/api/v2.0/indexers/all/results'.format(
            nefarious_settings.jackett_host, nefarious_settings.jackett_port), params={'apikey': nefarious_settings.jackett_token}, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(str(e))
        raise Exception('Could not connect to jackett')


def fetch_jackett_indexers(nefarious_settings: NefariousSettings) -> List[str]:
    """
    To get all Jackett indexers including their capabilities you can use t=indexers on the all indexer.
    To get only configured/unconfigured indexers you can also add configured=true/false as query parameter.
    """
    response = requests.get('http://{}:{}/api/v2.0/indexers/all/results/torznab/api'.format(
        nefarious_settings.jackett_host, nefarious_settings.jackett_port),
        params={
            'apikey': nefarious_settings.jackett_token,
            't': 'indexers',
            'configured': 'true',
        }, timeout=60)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    indexers = []
    for child in root:
        indexers.append(child.attrib['id'])
    return indexers


def get_best_torrent_result(results: list):
    best_result = None

    if results:

        # find the torrent result with the highest weight (i.e seeds)
        best_result = results[0]
        for result in results:
            if result['Seeders'] > best_result['Seeders']:
                best_result = result

    else:
        logging.info('No valid best search result')

    return best_result


def results_with_valid_urls(results: list, nefarious_settings: NefariousSettings):
    populated_results = []

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
        populated_results.append(result)

    return populated_results


def get_media_new_path_and_name(watch_media, torrent_name: str, is_single_file: bool) -> tuple:
    """
    Returns a tuple of the new name and the path.
    Movie - Single File:
        Input: "Rambo [scene-stuff].mkv"
        Output: ("Rambo (1982)", "Rambo (1982).mkv")
    Movie - Folder:
        Input: "Rambo [scene-stuff]"
        Output: (None, "Rambo (1982)")
    TV - Single Episode Folder:
        Input: "Rick and Morty - S03E14 [scene-stuff]"
        Output: ("Rick and Morty/Season 3/", "Rick and Morty - S03E14")
    TV - Single Episode File:
        Input: "Rick and Morty - S03E14 [scene-stuff].mkv"
        Output ("Rick and Morty/Season 3/", "Rick and Morty - S03E14.mkv")
    TV - Full Full Season Folder:
        Input: "Rick and Morty - Season 3 [scene-stuff]"
        Output: ("Rick and Morty/", "Rick and Morty - Season 3")
    """

    # movie
    if isinstance(watch_media, WatchMovie):
        name = '{} ({})'.format(watch_media, watch_media.release_date.year)
        dir_name = name if is_single_file else None

    # tv
    else:
        # full season
        if isinstance(watch_media, WatchTVSeason):
            season = watch_media  # type WatchTVSeason
            name = str(season)
            dir_name = str(season.watch_tv_show)
        # single episode
        elif isinstance(watch_media, WatchTVEpisode):
            episode = watch_media  # type WatchTVEpisode
            name = str(episode)
            dir_name = os.path.join(str(episode.watch_tv_show), 'Season {:02d}'.format(episode.season_number))
        else:
            raise Exception('unknown media')

    # maintain extension if torrent is a single file vs a directory
    if is_single_file:
        extension_match = regex.search(r'(\.\w+)$', torrent_name)
        if extension_match:
            extension = extension_match.group()
            name += extension

    name = sanitize_final_media_title(name)
    dir_name = sanitize_final_media_title(dir_name)

    return dir_name, name


def destroy_transmission_result(instance: WatchMediaBase):
    # delete transmission result, including data, if it still exists
    nefarious_settings = NefariousSettings.get()
    try:
        transmission_client = get_transmission_client(nefarious_settings)
        transmission_client.remove_torrent([instance.transmission_torrent_hash], delete_data=True, timeout=10)
    except Exception as e:
        logging.warning(str(e))
        logging.warning('could not destroy torrent in transmission')


def sanitize_final_media_title(title: str):
    # replace any colons (plex seems to have trouble with them)
    # Input: "The Lego Movie 2: The Second Part"
    # Output: "The Lego Movie 2 - The Second Part"
    if title:
        title = re.sub(r"\s*:+\s*", ' - ', title)
    return title
