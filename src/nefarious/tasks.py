import logging
import os
from celery import chain
from celery.signals import task_failure
from datetime import datetime
from celery_once import QueueOnce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date

from nefarious.celery import app
from nefarious.models import NefariousSettings, WatchMovie, WatchTVEpisode, WatchTVSeason, WatchTVSeasonRequest, WatchTVShow
from nefarious.processors import WatchMovieProcessor, WatchTVEpisodeProcessor, WatchTVSeasonProcessor
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client
from nefarious.utils import get_media_new_path_and_name
from nefarious import websocket
from nefarious import webhook


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
    'Auto Watch New TV Seasons': {
        'task': 'nefarious.tasks.auto_watch_new_seasons_task',
        'schedule': 60 * 60 * 24 * 7,
    },
    'Refresh TMDB Settings': {
        'task': 'nefarious.tasks.refresh_tmdb_configuration',
        'schedule': 60 * 60 * 24 * 1,
    },
}


@task_failure.connect
def log_exception(**kwargs):
    logging.error('TASK EXCEPTION', exc_info=kwargs['exception'])


@app.task(base=QueueOnce, once={'graceful': True})
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
        logging.info('Failed fetching entire season {} - falling back to individual episodes'.format(watch_tv_season))
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
                    release_date=parse_date(episode.get('air_date') or ''),
                )
            )

            # build list of tasks to execute
            watch_tv_episodes_tasks.append(watch_tv_episode_task.si(watch_tv_episode.id))

        # remove the "watch season" now that we've requested to fetch all individual episodes
        watch_tv_season.delete()

        # execute tasks sequentially
        chain(*watch_tv_episodes_tasks)()


@app.task(base=QueueOnce, once={'graceful': True})
def watch_tv_episode_task(watch_tv_episode_id: int):
    processor = WatchTVEpisodeProcessor(watch_media_id=watch_tv_episode_id)
    processor.fetch()


@app.task(base=QueueOnce, once={'graceful': True})
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
    nefarious_settings.tmdb_languages = configuration.languages()
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

                # get the sub path (ie. "movies/", "tv/') so we can move the data from staging
                sub_path = (
                    nefarious_settings.transmission_movie_download_dir if isinstance(media, WatchMovie)
                    else nefarious_settings.transmission_tv_download_dir
                ).lstrip('/')

                # get the path and updated name for the data
                new_path, new_name = get_media_new_path_and_name(media, torrent.name, len(torrent.files()) == 1)

                # move the data
                transmission_session = transmission_client.session_stats()
                move_to_path = os.path.join(
                    transmission_session.download_dir,
                    sub_path,
                    new_path or '',
                )
                logging.info('Moving torrent data to "{}"'.format(move_to_path))
                torrent.move_data(move_to_path)

                # rename the data
                logging.info('Renaming torrent file from "{}" to "{}"'.format(torrent.name, new_name))
                transmission_client.rename_torrent_path(torrent.id, torrent.name, new_name)

                # send websocket message media was updated
                media_type, data = websocket.get_media_type_and_serialized_watch_media(media)
                websocket.send_message(websocket.ACTION_UPDATED, media_type, data)

                # send complete message through webhook
                webhook.send_message('{} was downloaded'.format(media))


@app.task
def wanted_media_task():

    tasks = []
    wanted_kwargs = dict(collected=False, transmission_torrent_hash__isnull=True)

    #
    # scan for individual watch media
    #

    wanted_media_data = {
        'movie': {
            'query': WatchMovie.objects.filter(**wanted_kwargs),
            'task': watch_movie_task,
        },
        'season': {
            'query': WatchTVSeason.objects.filter(**wanted_kwargs),
            'task': watch_tv_show_season_task,
        },
        'episode': {
            'query': WatchTVEpisode.objects.filter(**wanted_kwargs),
            'task': watch_tv_episode_task,
        },
    }

    today = timezone.now().date()

    for media_type, data in wanted_media_data.items():
        for media in data['query']:
            # media has been released (or it's missing it's release date so try anyway) so create a task to try and fetch it
            if not media.release_date or media.release_date <= today:
                logging.info('Wanted {type}: {media}'.format(type=media_type, media=media))
                tasks.append(data['task'].si(media.id))
            # media has not been released so skip
            else:
                logging.info("Skipping wanted {type} since it hasn't aired yet: {media} ".format(type=media_type, media=media))

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
        last_air_date = parse_date(season.get('air_date') or '')  # season air date

        # otherwise add any new episodes to our watch list
        for episode in season['episodes']:
            episode_air_date = parse_date(episode.get('air_date') or '')

            # if episode air date exists, use as last air date
            if episode_air_date:
                last_air_date = episode_air_date if not last_air_date or episode_air_date > last_air_date else last_air_date

            watch_tv_episode, was_created = WatchTVEpisode.objects.get_or_create(
                watch_tv_show=tv_season_request.watch_tv_show,
                season_number=tv_season_request.season_number,
                episode_number=episode['episode_number'],
                defaults=dict(
                    # add non-unique constraint fields for the default values
                    tmdb_episode_id=episode['id'],
                    user=tv_season_request.user,
                    release_date=episode_air_date,
                ))
            if was_created:

                logging.info('adding newly found episode {} for {}'.format(episode['episode_number'], tv_season_request))

                # add episode to task queue
                tasks.append(watch_tv_episode_task.si(watch_tv_episode.id))

        # assume there's no new episodes for anything that's aired this long ago
        days_since_aired = (now.date() - last_air_date).days if last_air_date else 0
        if days_since_aired > 30:
            logging.warning('completing old tv season request {}'.format(tv_season_request))
            tv_season_request.collected = True
            tv_season_request.save()

    # execute tasks sequentially
    chain(*tasks)()


@app.task
def send_websocket_message_task(action: str, media_type: str, data: dict):
    websocket.send_message(action, media_type, data)


@app.task
def auto_watch_new_seasons_task():
    """
    look for newly aired seasons that the user wants to automatically watch
    """

    nefarious_settings = NefariousSettings.get()
    tmdb_client = get_tmdb_client(nefarious_settings)

    # cycle through every show that has auto-watch enabled
    for watch_show in WatchTVShow.objects.filter(auto_watch=True):
        tmdb_show = tmdb_client.TV(watch_show.tmdb_show_id)
        show_data = tmdb_show.info()

        added_season = False

        # find any season with a newer air date than the "auto watch" and queue it up
        for season in show_data['seasons']:
            air_date = parse_date(season['air_date'] or '')

            # air date is newer than our auto watch date
            if air_date and watch_show.auto_watch_date_updated and air_date >= watch_show.auto_watch_date_updated:

                # season & request params
                create_params = dict(
                    watch_tv_show=watch_show,
                    season_number=season['season_number'],
                    defaults=dict(
                        user=watch_show.user,
                        release_date=air_date,
                    )
                )

                # create a season request instance to keep up with slowly-released episodes
                WatchTVSeasonRequest.objects.get_or_create(**create_params)
                # also save a watch tv season instance to try and download the whole season immediately
                watch_tv_season, was_season_created = WatchTVSeason.objects.get_or_create(**create_params)

                # season was created
                if was_season_created:
                    added_season = True
                    logging.info('Automatically watching newly aired season {}'.format(watch_tv_season))
                    # send a websocket message for this new season
                    media_type, data = websocket.get_media_type_and_serialized_watch_media(watch_tv_season)
                    send_websocket_message_task.delay(websocket.ACTION_UPDATED, media_type, data)

                    # create a task to download the whole season (fallback to individual episodes if it fails)
                    watch_tv_show_season_task.delay(watch_tv_season.id)

        # new season added to show
        if added_season:
            # update auto watch date requested
            watch_show.auto_watch_date_updated = datetime.utcnow().date()
            watch_show.save()
