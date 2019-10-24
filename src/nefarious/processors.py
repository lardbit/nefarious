import os
import logging
from django.conf import settings
from datetime import datetime
from django.utils import dateparse
from nefarious.models import WatchMovie, NefariousSettings, TorrentBlacklist, WatchTVEpisode, WatchTVSeason
from nefarious.parsers.movie import MovieParser
from nefarious.parsers.tv import TVParser
from nefarious.quality import Profile
from nefarious.search import SearchTorrents, MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, SearchTorrentsCombined
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client
from nefarious.utils import get_best_torrent_result, results_with_valid_urls


class WatchProcessorBase:
    watch_media = None
    nefarious_settings: NefariousSettings = None

    tmdb_media = None
    tmdb_client = None
    transmission_client = None

    def __init__(self, watch_media_id: int):
        self.nefarious_settings = NefariousSettings.get()
        self.tmdb_client = get_tmdb_client(self.nefarious_settings)
        self.transmission_client = get_transmission_client(self.nefarious_settings)
        self.watch_media = self._get_watch_media(watch_media_id)
        self.tmdb_media = self._get_tmdb_media()

    def fetch(self):
        logging.info('Processing request to watch {}'.format(self.watch_media))
        valid_search_results = []
        search = self._get_search_results()

        # save this attempt date
        self.watch_media.last_attempt_date = datetime.utcnow()
        self.watch_media.save()

        if search.ok:

            for result in search.results:
                if self.is_match(result['Title']):
                    valid_search_results.append(result)
                else:
                    logging.info('Not matched: {}'.format(result['Title']))

            if valid_search_results:

                # trace the "torrent url" (sometimes magnet) in each valid result
                valid_search_results = self._results_with_valid_urls(valid_search_results)

                while valid_search_results:

                    logging.info('Valid Search Results: {}'.format(len(valid_search_results)))

                    # find the torrent result with the highest weight (i.e seeds)
                    best_result = self._get_best_torrent_result(valid_search_results)

                    transmission_client = get_transmission_client(self.nefarious_settings)
                    transmission_session = transmission_client.session_stats()

                    # add to transmission
                    torrent = transmission_client.add_torrent(
                        best_result['torrent_url'],
                        paused=True,  # start paused to we can verify if the torrent has been blacklisted
                        download_dir=self._get_download_dir(transmission_session),
                    )

                    # verify it's not blacklisted and save & start this torrent
                    if not TorrentBlacklist.objects.filter(hash=torrent.hashString).exists():
                        logging.info('Adding torrent for {}'.format(self.tmdb_media[self._get_tmdb_title_key()]))
                        logging.info('Added torrent {} with {} seeders'.format(best_result['Title'], best_result['Seeders']))
                        logging.info('Starting torrent id: {} and hash {}'.format(torrent.id, torrent.hashString))

                        # save torrent details on our watch instance
                        self._save_torrent_details(torrent)

                        # start the torrent
                        if not settings.DEBUG:
                            torrent.start()
                        return True
                    else:
                        # remove the blacklisted/paused torrent and continue to the next result
                        logging.info('BLACKLISTED: {} ({}) - trying next best result'.format(best_result['Title'], torrent.hashString))
                        transmission_client.remove_torrent([torrent.id])
                        valid_search_results.pop()
                        continue
            else:
                logging.info('No valid search results for {}'.format(self.tmdb_media[self._get_tmdb_title_key()]))
        else:
            logging.info('Search error: {}'.format(search.error_content))

        logging.info('Unable to find any results for {}'.format(self.tmdb_media[self._get_tmdb_title_key()]))

        return False

    def is_match(self, title: str) -> bool:
        parser = self._get_parser(title)

        # use custom quality profile if one exists
        if self.watch_media.quality_profile_custom:
            quality_profile = self.watch_media.quality_profile_custom
        else:
            quality_profile = self._get_quality_profile()

        profile = Profile.get_from_name(quality_profile)

        return (
            self._is_match(parser) and
            parser.is_quality_match(profile) and
            parser.is_hardcoded_subs_match(self.nefarious_settings.allow_hardcoded_subs) and
            parser.is_keyword_search_filter_match(
                self.nefarious_settings.keyword_search_filters.keys() if self.nefarious_settings.keyword_search_filters else []
            )
        )

    def _results_with_valid_urls(self, results: list):
        return results_with_valid_urls(results, self.nefarious_settings)

    def _get_best_torrent_result(self, results: list):
        return get_best_torrent_result(results)

    def _get_quality_profile(self):
        raise NotImplementedError

    def _get_watch_media(self, watch_media_id: int):
        raise NotImplementedError

    def _get_download_dir(self, transmission_session):
        raise NotImplementedError

    def _get_tmdb_media(self):
        raise NotImplementedError

    def _get_parser(self, title: str):
        raise NotImplementedError

    def _get_tmdb_title_key(self):
        raise NotImplementedError

    def _get_media_type(self) -> str:
        raise NotImplementedError

    def _save_torrent_details(self, torrent):
        self.watch_media.transmission_torrent_hash = torrent.hashString
        self.watch_media.save()

    def _is_match(self, parser) -> bool:
        raise NotImplementedError

    def _get_search_results(self):
        raise NotImplementedError


class WatchMovieProcessor(WatchProcessorBase):

    def _get_quality_profile(self):
        return self.nefarious_settings.quality_profile_movies

    def _get_parser(self, title: str):
        return MovieParser(title)

    def _is_match(self, parser):
        release_year = dateparse.parse_date(self.tmdb_media['release_date']).strftime('%Y')
        return parser.is_match(
            title=self.tmdb_media[self._get_tmdb_title_key()],
            year=release_year,
        )

    def _get_media_type(self) -> str:
        return MEDIA_TYPE_MOVIE

    def _get_download_dir(self, transmission_session):
        return os.path.join(
            transmission_session.download_dir, settings.UNPROCESSED_PATH, self.nefarious_settings.transmission_movie_download_dir.lstrip('/'))

    def _get_tmdb_title_key(self):
        return 'title'

    def _get_tmdb_media(self):
        movie_result = self.tmdb_client.Movies(self.watch_media.tmdb_movie_id)
        params = {
            'language': self.nefarious_settings.language,
        }
        movie = movie_result.info(**params)
        return movie

    def _get_watch_media(self, watch_media_id: int):
        watch_movie = WatchMovie.objects.get(pk=watch_media_id)
        return watch_movie

    def _get_search_results(self):
        media = self.tmdb_media
        return SearchTorrents(MEDIA_TYPE_MOVIE, media[self._get_tmdb_title_key()])


class WatchTVProcessorBase(WatchProcessorBase):

    def _get_quality_profile(self):
        return self.nefarious_settings.quality_profile_tv

    def _get_parser(self, title: str):
        return TVParser(title)

    def _get_media_type(self) -> str:
        return MEDIA_TYPE_TV

    def _get_download_dir(self, transmission_session):
        return os.path.join(
            transmission_session.download_dir, settings.UNPROCESSED_PATH, self.nefarious_settings.transmission_tv_download_dir.lstrip('/'))

    def _get_tmdb_title_key(self):
        return 'name'


class WatchTVEpisodeProcessor(WatchTVProcessorBase):
    """
    Single episode
    """
    show = None

    def _get_watch_media(self, watch_media_id: int):
        watch_episode = WatchTVEpisode.objects.get(pk=watch_media_id)
        return watch_episode

    def _is_match(self, parser):
        # supply show's name vs episode name for title matching
        return parser.is_match(
            title=self.show[self._get_tmdb_title_key()],
            season_number=self.tmdb_media['season_number'],
            episode_number=self.tmdb_media['episode_number'],
        )

    def _get_tmdb_media(self):
        # store show on instance
        show_result = self.tmdb_client.TV(self.watch_media.watch_tv_show.tmdb_show_id)
        params = {
            'language': self.nefarious_settings.language,
        }
        self.show = show_result.info(**params)

        episode_result = self.tmdb_client.TV_Episodes(self.watch_media.watch_tv_show.tmdb_show_id, self.watch_media.season_number, self.watch_media.episode_number)
        episode = episode_result.info(**params)
        return episode

    def _get_search_results(self):
        # query the show name AND the season/episode name separately
        # i.e search for "Atlanta" and "Atlanta s01e05" individually for best results
        watch_episode = self.watch_media  # type: WatchTVEpisode
        show_result = self.tmdb_client.TV(watch_episode.watch_tv_show.tmdb_show_id)
        params = {
            'language': self.nefarious_settings.language,
        }
        show = show_result.info(**params)

        return SearchTorrentsCombined([
            # search the show name
            SearchTorrents(MEDIA_TYPE_TV, show['name']),
            # search the show name and the season/episode combination
            SearchTorrents(MEDIA_TYPE_TV, '{} s{:02d}e{:02d}'.format(
                show['name'],
                self.tmdb_media['season_number'],
                self.tmdb_media['episode_number'],
            )),
        ])


class WatchTVSeasonProcessor(WatchTVProcessorBase):
    """
    Entire season
    """

    def _get_watch_media(self, watch_media_id: int):
        watch_season = WatchTVSeason.objects.get(pk=watch_media_id)
        return watch_season

    def _is_match(self, parser):
        return parser.is_match(
            title=self.tmdb_media[self._get_tmdb_title_key()],
            season_number=self.watch_media.season_number,
        )

    def _get_tmdb_media(self):
        show_result = self.tmdb_client.TV(self.watch_media.watch_tv_show.tmdb_show_id)
        params = {
            'language': self.nefarious_settings.language,
        }
        show = show_result.info(**params)
        return show

    def _get_search_results(self):
        media = self.tmdb_media
        return SearchTorrents(MEDIA_TYPE_TV, media[self._get_tmdb_title_key()])
