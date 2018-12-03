import logging
from nefarious.celery import app
from nefarious.models import NefariousSettings
from nefarious.processors import WatchMovieProcessor, WatchTVEpisodeProcessor, WatchTVShowProcessor
from nefarious.tmdb import get_tmdb_client


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
