import requests
from nefarious.models import NefariousSettings
from nefarious.utils import logger_background


def send_message(message: str):
    nefarious_settings = NefariousSettings.get()
    if nefarious_settings.webhook_url and nefarious_settings.webhook_key:
        response = requests.post(nefarious_settings.webhook_url, json={nefarious_settings.webhook_key: message}, timeout=5)
        try:
            response.raise_for_status()
        except Exception as e:
            logger_background.warning('webhook error for url {} and data key "{}"'.format(nefarious_settings.webhook_url, nefarious_settings.webhook_key))
            logger_background.exception(e)
