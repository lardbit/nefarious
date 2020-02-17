import json
import logging
from django.conf import settings
from websocket import create_connection

from nefarious.api.serializers import WatchMovieSerializer, WatchTVSeasonSerializer, WatchTVEpisodeSerializer
from nefarious.models import WatchMovie, WatchTVEpisode, WatchTVSeason

MEDIA_COMPLETE_MOVIE = 'MEDIA_COMPLETE_MOVIE'
MEDIA_COMPLETE_TV_SEASON = 'MEDIA_COMPLETE_TV_SEASON'
MEDIA_COMPLETE_TV_EPISODE = 'MEDIA_COMPLETE_TV_EPISODE'


def websocket_send_data(message: str, data: dict):
    try:
        ws = create_connection(settings.WEBSOCKET_URL, timeout=5)
        ws.send(json.dumps({
            'message': message,
            'data': data,
        }))
    except Exception as e:
        logging.exception(e)


def websocket_message_media_complete(media):
    if isinstance(media, WatchMovie):
        websocket_send_data(MEDIA_COMPLETE_MOVIE, WatchMovieSerializer(instance=media).data)
    elif isinstance(media, WatchTVSeason):
        websocket_send_data(MEDIA_COMPLETE_TV_SEASON, WatchTVSeasonSerializer(instance=media).data)
    elif isinstance(media, WatchTVEpisode):
        websocket_send_data(MEDIA_COMPLETE_TV_EPISODE, WatchTVEpisodeSerializer(instance=media).data)
