import logging
import requests
from nefarious.models import NefariousSettings


logger = logging.getLogger('nefarious')


def send_message(message: str):
    nefarious_settings = NefariousSettings.get()
    response = requests.post(nefarious_settings.webhook_url, json={nefarious_settings.webhook_key: message}, timeout=5)
    try:
        response.raise_for_status()
    except Exception as e:
        logger.warning('webhook error for url {} and data key "{}"'.format(nefarious_settings.webhook_url, nefarious_settings.webhook_key))
        logger.exception(e)
