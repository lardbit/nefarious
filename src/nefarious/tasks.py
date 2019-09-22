import logging
import os
from celery import chain
from celery.signals import task_failure
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from nefarious.celery import app
from nefarious.models import NefariousSettings, WatchMovie, WatchTVEpisode, WatchTVSeason, WatchTVSeasonRequest
from nefarious.processors import WatchMovieProcessor, WatchTVEpisodeProcessor, WatchTVSeasonProcessor
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client
from nefarious.utils import get_renamed_torrent

app.conf.beat_schedule = {
    'Completed Media Task': {
        'task': 'nefarious.tasks.completed_media_task',
        'schedule': 60 * 3,
    },
    'Wanted Media Task': {
        'task': 'nefarious.tasks.wanted_media_task',
        'schedule': 60 * 60 * 3,
    },
    'Wanted TV Seasons Task': {
        'task': 'nefarious.tasks.wanted_tv_season_task',
        'schedule': 60 * 60 * 24 * 1,
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

    watch_tv_season = get_object_or_404(WatchTVSeason, pk=watch_tv_season_id)

    # success so update the season request instance as "collected"
    if success:
        season_request = WatchTVSeasonRequest.objects.filter(
            watch_tv_show=watch_tv_season.watch_tv_show, season_number=watch_tv_season.season_number)
        if season_request.exists():
            season_request = season_request.first()
            season_request.collected = True
            season_request.save()
    # failed so delete season instance and fallback to trying individual episodes
    else:
        logging.info('Failed fetching season {} - falling back to individual episodes'.format(watch_tv_season))
        nefarious_settings = NefariousSettings.get()
        tmdb = get_tmdb_client(nefarious_settings)
        season_request = tmdb.TV_Seasons(watch_tv_season.watch_tv_show.tmdb_show_id, watch_tv_season.season_number)
        season = season_request.info()

        # save individual episode watches
        watch_tv_episodes_tasks = []
        for episode in season['episodes']:
            watch_tv_episode, was_created = WatchTVEpisode.objects.get_or_create(
                tmdb_episode_id=episode['id'],
                # add non-unique constraint fields for the default values
                defaults=dict(
                    user=watch_tv_season.user,
                    watch_tv_show=watch_tv_season.watch_tv_show,
                    season_number=watch_tv_season.season_number,
                    episode_number=episode['episode_number'],
                )
            )

            # build list of tasks to execute
            watch_tv_episodes_tasks.append(watch_tv_episode_task.si(watch_tv_episode.id))

        # remove the "watch season" now that we've requested to fetch all individual episodes
        watch_tv_season.delete()

        # execute tasks sequentially
        chain(*watch_tv_episodes_tasks)()


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
        except KeyError:
            # media's torrent reference no longer exists so remove the reference
            logging.info("Media's torrent no longer present, removing reference: {}".format(media))
            media.transmission_torrent_hash = None
            media.save()
        else:
            # download is complete
            if torrent.progress == 100:

                # flag media as completed
                logging.info('Media completed: {}'.format(media))
                media.collected = True
                media.collected_date = datetime.utcnow()
                media.save()

                # special handling for tv seasons
                if isinstance(media, WatchTVSeason):

                    # mark season request complete
                    for season_request in WatchTVSeasonRequest.objects.filter(watch_tv_show=media.watch_tv_show, season_number=media.season_number):
                        season_request.collected = True
                        season_request.save()

                    # delete any individual episodes now that we have the whole season
                    for episode in WatchTVEpisode.objects.filter(watch_tv_show=media.watch_tv_show, season_number=media.season_number):
                        episode.delete()

                # rename the torrent file/path
                renamed_torrent_name = get_renamed_torrent(torrent, media)
                logging.info('Renaming torrent file from "{}" to "{}"'.format(torrent.name, renamed_torrent_name))
                transmission_client.rename_torrent_path(torrent.id, torrent.name, renamed_torrent_name)

                # move data from staging path to actual complete path
                dir_name = (
                    nefarious_settings.transmission_movie_download_dir if isinstance(media, WatchMovie)
                    else nefarious_settings.transmission_tv_download_dir
                )
                transmission_session = transmission_client.session_stats()
                move_to_path = os.path.join(
                    transmission_session.download_dir,
                    dir_name.lstrip('/'),
                )
                logging.info('Moving torrent data to "{}"'.format(move_to_path))
                torrent.move_data(move_to_path)


@app.task
def wanted_media_task():

    wanted_kwargs = dict(collected=False, transmission_torrent_hash__isnull=True)

    #
    # individual watch media
    #

    wanted_movies = WatchMovie.objects.filter(**wanted_kwargs)
    wanted_tv_seasons = WatchTVSeason.objects.filter(**wanted_kwargs)
    wanted_tv_episodes = WatchTVEpisode.objects.filter(**wanted_kwargs)

    tasks = []

    for media in wanted_movies:
        logging.info('Wanted movie: {}'.format(media))
        tasks.append(watch_movie_task.si(media.id))

    for media in wanted_tv_seasons:
        logging.info('Wanted tv season: {}'.format(media))
        tasks.append(watch_tv_show_season_task.si(media.id))

    for media in wanted_tv_episodes:
        logging.info('Wanted tv episode: {}'.format(media))
        tasks.append(watch_tv_episode_task.si(media.id))

    # execute tasks sequentially
    chain(*tasks)()


@app.task
def wanted_tv_season_task():
    tasks = []
    nefarious_settings = NefariousSettings.get()
    tmdb = get_tmdb_client(nefarious_settings)

    #
    # re-check for requested tv seasons that have had new episodes released from TMDB (which was stale previously)
    #

    for tv_season_request in WatchTVSeasonRequest.objects.filter(collected=False):
        season_request = tmdb.TV_Seasons(tv_season_request.watch_tv_show.tmdb_show_id, tv_season_request.season_number)
        season = season_request.info()

        now = datetime.utcnow()
        last_air_date = parse_date(season['air_date'])  # season air date

        # otherwise add any new episodes to our watch list
        for episode in season['episodes']:
            episode_air_date = parse_date(episode['air_date'])
            last_air_date = episode_air_date if episode_air_date > last_air_date else last_air_date
            watch_tv_episode, was_created = WatchTVEpisode.objects.get_or_create(
                tmdb_episode_id=episode['id'],
                defaults=dict(
                    # add non-unique constraint fields for the default values
                    watch_tv_show=tv_season_request.watch_tv_show,
                    season_number=tv_season_request.season_number,
                    episode_number=episode['episode_number'],
                    user=tv_season_request.user,
                ))
            if was_created:
                watch_tv_episode.save()

                logging.info('adding newly found episode {} for {}'.format(episode['episode_number'], tv_season_request))

                # add episode to task queue
                tasks.append(watch_tv_episode_task.si(watch_tv_episode.id))

        # assume there's no new episodes for anything that's aired this long ago
        days_since_aired = (now.date() - last_air_date).days
        if days_since_aired > 30:
            logging.warning('completing old tv season request {}'.format(tv_season_request))
            tv_season_request.collected = True
            tv_season_request.save()

    # execute tasks sequentially
    chain(*tasks)()
