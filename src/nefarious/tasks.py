import logging
from datetime import datetime
from nefarious.celery import app
from nefarious.models import NefariousSettings, WatchMovie, WatchTVEpisode
from nefarious.processors import WatchMovieProcessor, WatchTVEpisodeProcessor, WatchTVShowProcessor
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client

app.conf.beat_schedule = {
    'Completed Media Task': {
        'task': 'nefarious.tasks.completed_media_task',
        'schedule': 60 * 5,
    },
    'Wanted Media Task': {
        'task': 'nefarious.tasks.wanted_media_task',
        'schedule': 60 * 60 * 2,
    },
}


@app.task
def watch_tv_show_season_task(watch_tv_show_id: int, season_number: int):
    processor = WatchTVShowProcessor(watch_media_id=watch_tv_show_id, season_number=season_number)
    processor.fetch()


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
    tv = WatchTVEpisode.objects.filter(**incomplete_kwargs)

    incomplete_media = list(movies) + list(tv)

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
    wanted_movies = WatchMovie.objects.filter(collected=False, transmission_torrent_hash__isnull=True)
    wanted_tv_episodes = WatchTVEpisode.objects.filter(collected=False, transmission_torrent_hash__isnull=True)

    countdown = 0
    for media in wanted_movies:
        logging.info('Wanted movie: {}'.format(media))
        watch_movie_task.s(media.id).apply_async(countdown=countdown)
        countdown += 60

    # TODO - should properly request entire season if that was originally requested
    countdown = 0
    for media in wanted_tv_episodes:
        logging.info('Wanted tv episode: {}'.format(media))
        watch_tv_episode_task.s(media.id).apply_async(countdown=countdown)
        countdown += 60
