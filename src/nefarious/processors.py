import os
import logging
from nefarious.models import WatchMovie, NefariousSettings, TorrentBlacklist
from nefarious.parsers.movie import MovieParser
from nefarious.search import SearchTorrents, MEDIA_TYPE_MOVIE
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client
from nefarious.utils import get_best_torrent_result


class WatchProcessorBase:
    watch_media = None
    nefarious_settings: NefariousSettings = None

    tmdb_media = None
    tmdb_client = None
    transmission_client = None

    def __init__(self, watch_media_id: int):
        self.nefarious_settings = NefariousSettings.objects.all().get()
        self.tmdb_client = get_tmdb_client(self.nefarious_settings)
        self.transmission_client = get_transmission_client(self.nefarious_settings)
        self.watch_media = self._get_watch_media(watch_media_id)
        self.tmdb_media = self._get_tmdb_media()

        parser_class = self._get_parser_class()
        search = self._get_search_results()
        valid_search_results = []

        if search.ok:

            for result in search.results['Results']:
                parser = parser_class(result['Title'])
                if parser.is_match(self.tmdb_media[self._get_tmdb_title_key()]):
                    valid_search_results.append(result)
                else:
                    logging.info('Not matched: {}'.format(result['Title']))

            if valid_search_results:

                while valid_search_results:

                    # find the torrent result with the highest weight (i.e seeds)
                    best_result = get_best_torrent_result(valid_search_results, self.nefarious_settings)

                    # add to transmission
                    transmission_client = get_transmission_client(self.nefarious_settings)
                    transmission_session = transmission_client.session_stats()

                    torrent = transmission_client.add_torrent(
                        best_result['torrent_url'],
                        paused=True,  # start paused so we can verify this torrent hasn't been blacklisted - then start it
                        download_dir=self._get_download_dir(transmission_session)
                    )

                    # verify it's not blacklisted and save & start this torrent
                    if not TorrentBlacklist.objects.filter(hash=torrent.hashString).exists():
                        logging.info('Adding torrent for {}'.format(self.tmdb_media[self._get_tmdb_title_key()]))
                        logging.info('Adding torrent {} with {} seeders'.format(best_result['Title'], best_result['Seeders']))
                        logging.info('Starting torrent id: {}'.format(torrent.id))

                        # save torrent details on our watch instance
                        self.watch_media.transmission_torrent_id = torrent.id
                        self.watch_media.transmission_torrent_hash = torrent.hashString
                        self.watch_media.save()

                        # start the torrent
                        torrent.start()
                        break
                    else:
                        # remove the blacklisted/paused torrent and continue to the next result
                        logging.info('BLACKLISTED: {} ({}) - trying next best result'.format(best_result['Title'], torrent.hashString))
                        transmission_client.remove_torrent([torrent.id])
                        valid_search_results.pop()
            else:
                logging.info('No valid search results for {}'.format(self.tmdb_media['original_title']))
        else:
            logging.info('Search error: {}'.format(search.error_content))

    def _get_watch_media(self, watch_media_id: int):
        raise NotImplementedError

    def _get_download_dir(self, transmission_session):
        raise NotImplementedError

    def _get_tmdb_media(self):
        raise NotImplementedError

    def _get_parser_class(self):
        raise NotImplementedError

    def _get_tmdb_title_key(self):
        raise NotImplementedError

    def _get_search_results(self):
        media = self.tmdb_media
        return SearchTorrents(MEDIA_TYPE_MOVIE, media[self._get_tmdb_title_key()])


class WatchMovieProcessor(WatchProcessorBase):

    def _get_download_dir(self, transmission_session):
        return os.path.join(
            transmission_session.download_dir, self.nefarious_settings.transmission_movie_download_dir.lstrip('/'))

    def _get_parser_class(self):
        return MovieParser

    def _get_tmdb_title_key(self):
        return 'original_title_key'

    def _get_tmdb_media(self):
        movie_result = self.tmdb_client.Movies(self.watch_media.tmdb_movie_id)
        movie = movie_result.info()
        return movie

    def _get_watch_media(self, watch_media_id: int):
        watch_movie = WatchMovie.objects.get(pk=watch_media_id)
        return watch_movie
