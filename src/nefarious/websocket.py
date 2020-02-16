import json
import logging
from django.conf import settings
from websocket import create_connection


MESSAGE_MEDIA_COMPLETE = 'MEDIA_COMPLETE'


def websocket_send_data(data: dict):
    try:
        ws = create_connection(settings.WEBSOCKET_URL, timeout=5)
        ws.send(json.dumps(data))
    except Exception as e:
        logging.exception(e)
