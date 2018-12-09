import logging
from datetime import datetime
from nefarious.celery import app
from nefarious.models import NefariousSettings, WatchMovie, WatchTVEpisode
from nefarious.processors import WatchMovieProcessor, WatchTVEpisodeProcessor, WatchTVShowProcessor
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client


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

    movies = WatchMovie.objects.filter(collected=False)
    movies = movies.exclude(transmission_torrent_hash__isnull=True)
    movies = movies.exclude(transmission_torrent_hash__exact='')
    tv = WatchTVEpisode.objects.filter(collected=False)
    tv = tv.exclude(transmission_torrent_hash__isnull=True)
    tv = tv.exclude(transmission_torrent_hash__exact='')

    uncollected_media = list(movies) + list(tv)

    for media in uncollected_media:
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
