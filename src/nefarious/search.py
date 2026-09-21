import requests
from defusedxml.common import DefusedXmlException
import defusedxml.ElementTree as ET
from typing import List
from nefarious.jackett import get_jackett_search_url
from nefarious.models import NefariousSettings
from nefarious.utils import logger_background

SEARCH_MEDIA_TYPE_TV = 'tv'
SEARCH_MEDIA_TYPE_MOVIE = 'movie'
TORZNAB_NAMESPACE = '{http://torznab.com/schemas/2015/feed}'


class SearchTorrents:
    def __init__(self, media_type: str, query: str):
        assert media_type in [SEARCH_MEDIA_TYPE_TV, SEARCH_MEDIA_TYPE_MOVIE]
        self.nefarious_settings = NefariousSettings.get()
        self.results = []
        self.ok = False
        self.error_content = None
        self.media_type = media_type
        self.query = query

        self.ok, self.results, self.error_content = self._request_with_retry()

    def _request_with_retry(self):
        errors = []
        for attempt in range(2):
            try:
                return True, self._request_results(), None
            except requests.Timeout as error:
                errors.append(str(error))
                logger_background.warning(
                    'Jackett search failed for filter %s on attempt %s: %s',
                    self.nefarious_settings.jackett_filter_index or 'all',
                    attempt + 1,
                    error,
                )
            except (requests.RequestException, ET.ParseError, DefusedXmlException, ValueError) as error:
                errors.append(str(error))
                logger_background.warning(
                    'Jackett search failed for filter %s: %s',
                    self.nefarious_settings.jackett_filter_index or 'all',
                    error,
                )
                break

        return False, [], '; '.join(errors)

    def _request_results(self) -> list:
        params = {
            'apikey': self.nefarious_settings.jackett_token,
            't': 'search' if self.media_type == SEARCH_MEDIA_TYPE_MOVIE else 'tvsearch',
            'q': self.query,
            'cat': ','.join(str(category) for category in self._categories(self.media_type)),
        }

        response = requests.get(
            get_jackett_search_url(self.nefarious_settings),
            params=params,
            timeout=self.nefarious_settings.jackett_search_timeout,
        )
        logger_background.info('jackett search: query=%s, url=%s', self.query, response.url)
        response.raise_for_status()
        return self._parse_results(response.content)

    @staticmethod
    def _safe_int(raw, default: int = 0) -> int:
        try:
            return int(raw)
        except (TypeError, ValueError, OverflowError):
            try:
                return int(float(raw))
            except (TypeError, ValueError, OverflowError):
                return default

    @staticmethod
    def _parse_results(content: bytes) -> list:
        root = ET.fromstring(content)
        if root.tag == 'error':
            raise ValueError(root.attrib.get('description', 'Jackett search failed'))

        results = []
        for item_position, item in enumerate(root.findall('./channel/item')):
            attributes = {
                attribute.attrib.get('name'): attribute.attrib.get('value')
                for attribute in item.findall('{}attr'.format(TORZNAB_NAMESPACE))
            }
            title = item.findtext('title') or ''
            link = item.findtext('link') or ''
            indexer = item.find('jackettindexer')
            tracker_id = indexer.attrib.get('id') if indexer is not None else None
            guid = item.findtext('guid') or link
            if not guid:
                guid = 'jackett-result:{}:{}:{}'.format(tracker_id or '', title, item_position)
            results.append({
                'Title': title,
                'Guid': guid,
                'Link': link,
                'MagnetUri': attributes.get('magneturl') or (link if link.startswith('magnet:') else None),
                'Size': SearchTorrents._safe_int(item.findtext('size')),
                'Seeders': SearchTorrents._safe_int(attributes.get('seeders')),
                'Tracker': indexer.text if indexer is not None else '',
                'TrackerId': tracker_id,
            })
        return results

    def _categories(self, media_type: str) -> list:
        # https://github.com/nZEDb/nZEDb/blob/dev/docs/newznab_api_specification.txt
        cat_movies = [2000, 2010, 2030, 2040, 2050, 2060, 2070]
        cat_tv = [5000, 5010, 5020, 5030, 5040, 5060, 5070, 5080]
        if media_type == SEARCH_MEDIA_TYPE_MOVIE:
            return cat_movies
        else:
            return cat_tv


class SearchTorrentsCombined:
    def __init__(self, search_torrents: List[SearchTorrents]):
        self.results: list = []
        self.ok = any([search.ok for search in search_torrents])
        self.error_content = ''

        for search in search_torrents:
            if search.ok:
                self.results += search.results
            else:
                self.error_content += '\n{}'.format(search.error_content)
