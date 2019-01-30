import logging
import regex
from celery import chain
from celery.signals import task_failure
from datetime import datetime
from django.shortcuts import get_object_or_404
from nefarious.celery import app
from nefarious.models import NefariousSettings, WatchMovie, WatchTVEpisode, WatchTVSeason
from nefarious.parsers.base import ParserBase
from nefarious.processors import WatchMovieProcessor, WatchTVEpisodeProcessor, WatchTVSeasonProcessor
from nefarious.search import SearchTorrents, MEDIA_TYPE_MOVIE
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client
from nefarious.utils import trace_torrent_url, swap_jackett_host, results_with_valid_urls, get_best_torrent_result, get_seed_only_indexers

app.conf.beat_schedule = {
    'Completed Media Task': {
        'task': 'nefarious.tasks.completed_media_task',
        'schedule': 60 * 3,
    },
    'Wanted Media Task': {
        'task': 'nefarious.tasks.wanted_media_task',
        'schedule': 60 * 60 * 2,
    },
    'Refresh TMDB Settings': {
        'task': 'nefarious.tasks.refresh_tmdb_configuration',
        'schedule': 60 * 60 * 24 * 1,
    },
}


@task_failure.connect
def log_exception(**kwargs):
    logging.error('TASK EXCEPTION', exc_info=kwargs['exception'])


@app.task
def watch_tv_show_season_task(watch_tv_season_id: int):
    processor = WatchTVSeasonProcessor(watch_media_id=watch_tv_season_id)
    success = processor.fetch()

    # delete watch_tv_season and fallback to individual episodes
    if not success:
        watch_tv_season = get_object_or_404(WatchTVSeason, pk=watch_tv_season_id)
        logging.info('Failed fetching season {} - falling back to individual episodes'.format(watch_tv_season))
        nefarious_settings = NefariousSettings.get()
        tmdb = get_tmdb_client(nefarious_settings)
        season_request = tmdb.TV_Seasons(watch_tv_season.watch_tv_show.tmdb_show_id, watch_tv_season.season_number)
        season = season_request.info()

        # save individual episode watches
        watch_tv_episodes = []
        for episode in season['episodes']:
            watch_tv_episode, was_created = WatchTVEpisode.objects.get_or_create(
                user=watch_tv_season.user,
                watch_tv_show=watch_tv_season.watch_tv_show,
                tmdb_episode_id=episode['id'],
                season_number=watch_tv_season.season_number,
                episode_number=episode['episode_number'],
            )
            watch_tv_episodes.append(watch_tv_episode)

        countdown = 0
        for watch_tv_episode in watch_tv_episodes:
            watch_tv_episode_task.s(watch_tv_episode.id).apply_async(countdown=countdown)
            countdown += 15

        # remove the "watch season" now that we've requested to fetch all individual episodes
        watch_tv_season.delete()


@app.task
def watch_tv_episode_task(watch_tv_episode_id: int):
    processor = WatchTVEpisodeProcessor(watch_media_id=watch_tv_episode_id)
    processor.fetch()


@app.task
def watch_movie_task(watch_movie_id: int):
    processor = WatchMovieProcessor(watch_media_id=watch_movie_id)
    processor.fetch()


@app.task
def refresh_tmdb_configuration():

    logging.info('Refreshing TMDB Configuration')

    nefarious_settings = NefariousSettings.get()

    tmdb_client = get_tmdb_client(nefarious_settings)
    configuration = tmdb_client.Configuration()

    nefarious_settings.tmdb_configuration = configuration.info()
    nefarious_settings.save()

    return nefarious_settings.tmdb_configuration


@app.task
def completed_media_task():
    nefarious_settings = NefariousSettings.get()
    transmission_client = get_transmission_client(nefarious_settings)

    incomplete_kwargs = dict(collected=False, transmission_torrent_hash__isnull=False)

    movies = WatchMovie.objects.filter(**incomplete_kwargs)
    tv_seasons = WatchTVSeason.objects.filter(**incomplete_kwargs)
    tv_episodes = WatchTVEpisode.objects.filter(**incomplete_kwargs)

    incomplete_media = list(movies) + list(tv_episodes) + list(tv_seasons)

    for media in incomplete_media:
        try:
            torrent = transmission_client.get_torrent(media.transmission_torrent_hash)
            if torrent.progress == 100:
                logging.info('Media completed: {}'.format(media))
                media.collected = True
                media.collected_date = datetime.utcnow()
                media.save()
        except KeyError:
            logging.info("Media's torrent no longer present, removing reference: {}".format(media))
            media.transmission_torrent_hash = None
            media.save()


@app.task
def wanted_media_task():

    wanted_kwargs = dict(collected=False, transmission_torrent_hash__isnull=True)

    wanted_movies = WatchMovie.objects.filter(**wanted_kwargs)
    wanted_tv_episodes = WatchTVEpisode.objects.filter(**wanted_kwargs)

    tasks = []

    for media in wanted_movies:
        logging.info('Wanted movie: {}'.format(media))
        tasks.append(watch_movie_task.si(media.id))

    for media in wanted_tv_episodes:
        logging.info('Wanted tv episode: {}'.format(media))
        tasks.append(watch_tv_episode_task.si(media.id))

    # execute tasks sequentially
    chain(*tasks)()


@app.task
def cross_seed_task(torrent_hash: str):
    # TODO - this isn't used and is a work in progress

    nefarious_settings = NefariousSettings.get()
    transmission_client = get_transmission_client(nefarious_settings)

    try:
        torrent = transmission_client.get_torrent(torrent_hash)
    except KeyError:
        logging.warning('{} no longer in transmission'.format(torrent_hash))
        return

    logging.info('Attempting cross seed for {}'.format(torrent.name))

    valid_results = []

    search = SearchTorrents(MEDIA_TYPE_MOVIE, torrent.name, search_seed_only=True)
    if search.ok:
        for result in search.results:
            transmission_client.add_torrent()
            normalized_title = regex.sub(ParserBase.word_delimiter_regex, ' ', torrent.name)
            if result['Title'].lower() in [torrent.name.lower(), normalized_title.lower()]:
                # TODO - the sizes won't match due to the inaccuracy of the scraping values
                # add paused torrent and verify the sizes match
                valid_results.append(result)

    # trace the "torrent url" (sometimes magnet) in each valid result
    valid_results = results_with_valid_urls(valid_results, nefarious_settings)

    logging.info(valid_results)

    seed_only_indexers = get_seed_only_indexers(nefarious_settings)

    if valid_results:
        for seed_only_indexer in seed_only_indexers:

            logging.info('Looking for cross seed results for indexer {}'.format(seed_only_indexer))

            # filter results to this seed-only indexer
            indexer_results = [r for r in valid_results if r['TrackerId'] == seed_only_indexer]
            if not indexer_results:
                logging.info('Indexer {} does not have any results for {}'.format(seed_only_indexer, torrent.name))
                continue

            # get the "best" result
            best_result = get_best_torrent_result(indexer_results)

            logging.info('Cross seeding {} for indexer {}'.format(best_result['Title'], best_result['Tracker']))

            # add a new key to our result object with the traced torrent url
            best_result['torrent_url'] = best_result['MagnetUri'] or trace_torrent_url(
                swap_jackett_host(best_result['Link'], nefarious_settings))

            # add to transmission
            transmission_session = transmission_client.session_stats()
            torrent = transmission_client.add_torrent(
                best_result['torrent_url'],
                paused=True,  # TODO
                # TODO
                #download_dir=self._get_download_dir(transmission_session)
            )
    else:
        logging.info('No valid cross seeding options for {}'.format(torrent.name))
