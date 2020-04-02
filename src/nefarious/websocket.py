import json
import logging
from django.conf import settings
from websocket import create_connection

from nefarious.api.serializers import (
    WatchMovieSerializer, WatchTVSeasonSerializer, WatchTVEpisodeSerializer, WatchTVSeasonRequestSerializer, WatchTVShowSerializer)
from nefarious.models import WatchMovie, WatchTVEpisode, WatchTVSeason, WatchTVSeasonRequest, WatchMediaBase, WatchTVShow

ACTION_UPDATED = 'UPDATED'
ACTION_REMOVED = 'REMOVED'

MEDIA_TYPE_MOVIE = 'MOVIE'
MEDIA_TYPE_TV_SHOW = 'TV_SHOW'
MEDIA_TYPE_TV_SEASON = 'TV_SEASON'
MEDIA_TYPE_TV_SEASON_REQUEST = 'TV_SEASON_REQUEST'
MEDIA_TYPE_TV_EPISODE = 'TV_EPISODE'


def send_message(action: str, media_type: str, data: dict):
    logging.info('Sending "{}" websocket message for media type {}'.format(action, media_type))
    if not settings.DEBUG:
        try:
            ws = create_connection(settings.WEBSOCKET_URL, timeout=5)
            ws.send(json.dumps({
                'action': action,
                'type': media_type,
                'data': data,
            }))
        except Exception as e:
            logging.error('Failed connecting to websocket server: {}'.format(settings.WEBSOCKET_URL))
            logging.exception(e)


def send_media_message(action: str, media: WatchMediaBase):
    media_type, data = get_media_type_and_serialized_watch_media(media)
    send_message(action, media_type, data)


def get_media_type_and_serialized_watch_media(media) -> tuple:
    if isinstance(media, WatchMovie):
        return MEDIA_TYPE_MOVIE, WatchMovieSerializer(instance=media).data
    elif isinstance(media, WatchTVShow):
        return MEDIA_TYPE_TV_SHOW, WatchTVShowSerializer(instance=media).data
    elif isinstance(media, WatchTVSeason):
        return MEDIA_TYPE_TV_SEASON, WatchTVSeasonSerializer(instance=media).data
    elif isinstance(media, WatchTVSeasonRequest):
        return MEDIA_TYPE_TV_SEASON_REQUEST, WatchTVSeasonRequestSerializer(instance=media).data
    elif isinstance(media, WatchTVEpisode):
        return MEDIA_TYPE_TV_EPISODE, WatchTVEpisodeSerializer(instance=media).data
    raise Exception('Unknown watch media type: {}'.format(type(media)))
