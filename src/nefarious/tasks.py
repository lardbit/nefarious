import logging
from celery import chain
from celery.signals import task_failure
from datetime import datetime
from django.shortcuts import get_object_or_404
from nefarious.celery import app
from nefarious.models import NefariousSettings, WatchMovie, WatchTVEpisode, WatchTVSeason
from nefarious.processors import WatchMovieProcessor, WatchTVEpisodeProcessor, WatchTVSeasonProcessor
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client

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
        nefarious_settings = NefariousSettings.singleton()
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

    nefarious_settings = NefariousSettings.singleton()

    tmdb_client = get_tmdb_client(nefarious_settings)
    configuration = tmdb_client.Configuration()

    nefarious_settings.tmdb_configuration = configuration.info()
    nefarious_settings.save()

    return nefarious_settings.tmdb_configuration


@app.task
def completed_media_task():
    nefarious_settings = NefariousSettings.singleton()
    transmission_client = get_transmission_client(nefarious_settings)

    incomplete_kwargs = dict(collected=False, transmission_torrent_hash__isnull=False)

    movies = WatchMovie.objects.filter(**incomplete_kwargs)
    tv_seasons = WatchTVSeason.objects.filter(**incomplete_kwargs)
    tv_episodes = WatchTVEpisode.objects.filter(**incomplete_kwargs)

    incomplete_media = list(movies) + list(tv_episodes) + list(tv_seasons)

    for media in incomplete_media:
        logging.info('Media not flagged completed: {}'.format(media))
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
