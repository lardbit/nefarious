from typing import Dict, List
import defusedxml.ElementTree as ET

import requests

from nefarious.models import NefariousSettings


def get_jackett_base_url(nefarious_settings: NefariousSettings) -> str:
    return "http://{}:{}".format(
        nefarious_settings.jackett_host,
        nefarious_settings.jackett_port,
    )


def get_jackett_search_url(nefarious_settings: NefariousSettings, indexer_id: str = None) -> str:
    return "{}/api/v2.0/indexers/{}/results/torznab".format(
        get_jackett_base_url(nefarious_settings),
        # https://github.com/Jackett/Jackett#filter-indexers
        indexer_id or nefarious_settings.jackett_filter_index or 'all',
    )


def get_jackett_session(nefarious_settings: NefariousSettings) -> requests.Session:
    session = requests.Session()
    timeout = nefarious_settings.jackett_search_timeout
    base_url = get_jackett_base_url(nefarious_settings)

    login_response = session.get('{}/UI/Login'.format(base_url), timeout=timeout)
    login_response.raise_for_status()

    if nefarious_settings.jackett_admin_password:
        login_response = session.post(
            '{}/UI/Dashboard'.format(base_url),
            data={'password': nefarious_settings.jackett_admin_password},
            timeout=timeout,
        )
        login_response.raise_for_status()

    return session


def get_jackett_indexers(nefarious_settings: NefariousSettings) -> List[Dict]:
    session = get_jackett_session(nefarious_settings)
    response = session.get(
        '{}/api/v2.0/indexers'.format(get_jackett_base_url(nefarious_settings)),
        params={'configured': 'true'},
        timeout=nefarious_settings.jackett_search_timeout,
    )
    response.raise_for_status()
    indexers = response.json()
    if not isinstance(indexers, list):
        raise ValueError('Jackett returned an invalid configured-indexers response')
    return indexers


def get_filtered_jackett_indexers(nefarious_settings: NefariousSettings) -> List[Dict[str, str]]:
    response = requests.get(
        get_jackett_search_url(nefarious_settings),
        params={
            'apikey': nefarious_settings.jackett_token,
            't': 'indexers',
            'configured': 'true',
        },
        timeout=nefarious_settings.jackett_search_timeout,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    if root.tag == 'error':
        raise ValueError(root.attrib.get('description', 'Jackett indexer lookup failed'))

    return [
        {
            'id': indexer.attrib['id'],
            'name': indexer.findtext('title') or indexer.attrib['id'],
        }
        for indexer in root.findall('indexer')
    ]
