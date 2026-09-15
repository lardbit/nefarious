import requests
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache
import xml.etree.ElementTree as ET
from typing import List
from nefarious.jackett import get_filtered_jackett_indexers, get_jackett_search_url
from nefarious.models import JackettIndexer, NefariousSettings
from nefarious.utils import logger_background

SEARCH_MEDIA_TYPE_TV = 'tv'
SEARCH_MEDIA_TYPE_MOVIE = 'movie'
TORZNAB_NAMESPACE = '{http://torznab.com/schemas/2015/feed}'
INDEXER_FAILURE_CACHE_TTL = 60 * 60 * 6
INDEXER_FAILURE_SERIAL_THRESHOLD = 3
MAX_PARALLEL_INDEXERS = 32


class SearchTorrents:
    def __init__(self, media_type: str, query: str):
        assert media_type in [SEARCH_MEDIA_TYPE_TV, SEARCH_MEDIA_TYPE_MOVIE]
        self.nefarious_settings = NefariousSettings.get()
        self.results = []
        self.ok = False
        self.error_content = None
        self.media_type = media_type
        self.query = query

        if self.nefarious_settings.jackett_serialize_flaresolverr_indexers:
            self._search_with_isolated_indexers()
        else:
            self.ok, self.results, self.error_content = self._request_with_retry()

    def _request_with_retry(self, indexer_id: str = None):
        errors = []
        for attempt in range(2):
            try:
                results = self._request_results(indexer_id)
                if indexer_id:
                    self._reset_indexer_failures(indexer_id)
                return True, results, None
            except requests.Timeout as error:
                errors.append(str(error))
                logger_background.warning(
                    'Jackett search failed for indexer %s on attempt %s: %s',
                    indexer_id or self.nefarious_settings.jackett_filter_index or 'all',
                    attempt + 1,
                    error,
                )
            except (requests.RequestException, ET.ParseError, ValueError) as error:
                errors.append(str(error))
                logger_background.warning(
                    'Jackett search failed for indexer %s: %s',
                    indexer_id or self.nefarious_settings.jackett_filter_index or 'all',
                    error,
                )
                break

        if indexer_id:
            self._record_indexer_failure(indexer_id)
        return False, [], '; '.join(errors)

    def _request_results(self, indexer_id: str = None) -> list:
        params = {
            'apikey': self.nefarious_settings.jackett_token,
            't': 'search' if self.media_type == SEARCH_MEDIA_TYPE_MOVIE else 'tvsearch',
            'q': self.query,
            'cat': ','.join(str(category) for category in self._categories(self.media_type)),
        }

        response = requests.get(
            get_jackett_search_url(self.nefarious_settings, indexer_id),
            params=params,
            timeout=self.nefarious_settings.jackett_search_timeout,
        )
        logger_background.info('jackett search: query=%s, url=%s', self.query, response.url)
        response.raise_for_status()
        return self._parse_results(response.content)

    def _search_with_isolated_indexers(self):
        try:
            indexers = get_filtered_jackett_indexers(self.nefarious_settings)
        except (requests.RequestException, ET.ParseError, ValueError) as error:
            logger_background.warning(
                'Could not enumerate filtered Jackett indexers; falling back to aggregate search: %s',
                error,
            )
            self.ok, self.results, self.error_content = self._request_with_retry()
            return

        metadata = {
            indexer.indexer_id: indexer
            for indexer in JackettIndexer.objects.filter(
                indexer_id__in=[indexer['id'] for indexer in indexers]
            )
        }
        parallel_ids = []
        serial_ids = []
        for indexer in indexers:
            indexer_id = indexer['id']
            indexer_metadata = metadata.get(indexer_id)
            should_serialize = (
                indexer_metadata is not None and indexer_metadata.effective_is_flaresolverr
            ) or self._get_indexer_failure_count(indexer_id) >= INDEXER_FAILURE_SERIAL_THRESHOLD
            (serial_ids if should_serialize else parallel_ids).append(indexer_id)

        outcomes = []
        if parallel_ids:
            with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL_INDEXERS, len(parallel_ids))) as executor:
                outcomes.extend(executor.map(self._request_with_retry, parallel_ids))

        for indexer_id in serial_ids:
            outcomes.append(self._request_with_retry(indexer_id))

        self.ok = any(outcome[0] for outcome in outcomes) if outcomes else True
        self.results = self._deduplicate_results([
            result
            for outcome in outcomes if outcome[0]
            for result in outcome[1]
        ])
        errors = [outcome[2] for outcome in outcomes if not outcome[0]]
        self.error_content = '\n'.join(errors) if errors else None

    @staticmethod
    def _parse_results(content: bytes) -> list:
        root = ET.fromstring(content)
        if root.tag == 'error':
            raise ValueError(root.attrib.get('description', 'Jackett search failed'))

        results = []
        for item in root.findall('./channel/item'):
            attributes = {
                attribute.attrib.get('name'): attribute.attrib.get('value')
                for attribute in item.findall('{}attr'.format(TORZNAB_NAMESPACE))
            }
            link = item.findtext('link') or ''
            indexer = item.find('jackettindexer')
            results.append({
                'Title': item.findtext('title') or '',
                'Guid': item.findtext('guid') or link,
                'Link': link,
                'MagnetUri': attributes.get('magneturl') or (link if link.startswith('magnet:') else None),
                'Size': int(item.findtext('size') or 0),
                'Seeders': int(attributes.get('seeders') or 0),
                'Tracker': indexer.text if indexer is not None else '',
                'TrackerId': indexer.attrib.get('id') if indexer is not None else None,
            })
        return results

    @staticmethod
    def _deduplicate_results(results: list) -> list:
        deduplicated = {}
        for result in results:
            deduplicated[result['Guid']] = result
        return list(deduplicated.values())

    @staticmethod
    def _failure_cache_key(indexer_id: str) -> str:
        return 'jackett:indexer:failure-count:{}'.format(indexer_id)

    def _get_indexer_failure_count(self, indexer_id: str) -> int:
        try:
            return int(cache.get(self._failure_cache_key(indexer_id), 0))
        except Exception as error:
            logger_background.warning('Could not read Jackett slow-indexer state: %s', error)
            return 0

    def _record_indexer_failure(self, indexer_id: str):
        try:
            cache_key = self._failure_cache_key(indexer_id)
            cache.set(
                cache_key,
                self._get_indexer_failure_count(indexer_id) + 1,
                timeout=INDEXER_FAILURE_CACHE_TTL,
            )
        except Exception as error:
            logger_background.warning('Could not store Jackett slow-indexer state: %s', error)

    def _reset_indexer_failures(self, indexer_id: str):
        try:
            cache.delete(self._failure_cache_key(indexer_id))
        except Exception as error:
            logger_background.warning('Could not reset Jackett slow-indexer state: %s', error)

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
