import json
import logging

import redis
from django.conf import settings

from nefarious.api.serializers import (
    WatchMovieSerializer, WatchTVSeasonSerializer, WatchTVEpisodeSerializer, WatchTVSeasonRequestSerializer, WatchTVShowSerializer)
from nefarious.models import WatchMovie, WatchTVEpisode, WatchTVSeason, WatchTVSeasonRequest, WatchTVShow, MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV_SHOW, \
    MEDIA_TYPE_TV_SEASON, MEDIA_TYPE_TV_SEASON_REQUEST, MEDIA_TYPE_TV_EPISODE

logger_background = logging.getLogger('nefarious-background')

ACTION_UPDATED = 'UPDATED'
ACTION_REMOVED = 'REMOVED'

# single channel broadcast to every connected client; media is a shared watchlist (not per-user)
EVENTS_CHANNEL = 'nefarious-media-updates'


def publish_media_event(action: str, media_type: str, data: dict):
    payload = json.dumps({
        'action': action,
        'type': media_type,
        'data': data,
    })
    try:
        client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        client.publish(EVENTS_CHANNEL, payload)
    except Exception as e:
        logger_background.error('Error publishing media event: {}'.format(e))


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
