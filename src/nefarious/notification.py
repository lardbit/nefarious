import apprise
from nefarious.utils import logger_background
from nefarious.models import NefariousSettings
from apprise import NotifyFormat, NotifyType


def send_message(message: str, title: str):
    # apprise notifications - https://github.com/caronc/apprise
    nefarious_settings = NefariousSettings.get()
    if nefarious_settings.apprise_notification_url:
        apprise_instance = apprise.Apprise()
        apprise_instance.add(nefarious_settings.apprise_notification_url)
        try:
            apprise_instance.notify(
                body=message,
                title=title,
                body_format=NotifyFormat.TEXT,
                notify_type=NotifyType.SUCCESS,
            )
        except Exception as e:
            logger_background.warning('apprise notification error for url {}'.format(nefarious_settings.apprise_notification_url))
            logger_background.exception(e)
            return
