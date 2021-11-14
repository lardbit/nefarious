import apprise
from nefarious.utils import logger_background
from nefarious.models import NefariousSettings


def send_message(message: str) -> bool:
    # apprise notifications - https://github.com/caronc/apprise
    nefarious_settings = NefariousSettings.get()
    if nefarious_settings.apprise_notification_url:
        apprise_instance = apprise.Apprise()
        apprise_instance.add(nefarious_settings.apprise_notification_url)
        try:
            return apprise_instance.notify(
                body=message,
            )
        except Exception as e:
            logger_background.warning('apprise notification error for url {}'.format(nefarious_settings.apprise_notification_url))
            logger_background.exception(e)
            return False
    return False
