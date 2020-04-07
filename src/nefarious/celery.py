from __future__ import absolute_import, unicode_literals
from django.conf import settings
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nefarious.settings')

app = Celery('nefarious', broker='redis://{}:{}/0'.format(
    settings.REDIS_HOST,
    settings.REDIS_PORT,
))
# celery-once
# https://github.com/cameronmaske/celery-once#usage
app.conf.ONCE = {
  'backend': 'celery_once.backends.Redis',
  'settings': {
    'url': 'redis://{host}:{port}/0'.format(host=settings.REDIS_HOST, port=settings.REDIS_PORT),
    'default_timeout': 60 * 60 * 6,
  }
}

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
