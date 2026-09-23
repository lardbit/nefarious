from typing import Dict, List
import defusedxml.ElementTree as ET

import requests

from nefarious.models import NefariousSettings


def get_jackett_base_url(nefarious_settings: NefariousSettings) -> str:
    return "http://{}:{}".format(
        nefarious_settings.jackett_host,
        nefarious_settings.jackett_port,
    )


def get_jackett_search_url(nefarious_settings: NefariousSettings) -> str:
    return "{}/api/v2.0/indexers/{}/results/torznab".format(
        get_jackett_base_url(nefarious_settings),
        # https://github.com/Jackett/Jackett#filter-indexers
        nefarious_settings.jackett_filter_index or 'all',
    )


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
