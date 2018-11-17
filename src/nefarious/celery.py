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

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

#app.conf.beat_schedule = {
#    'add-every-60-seconds': {
#        'task': 'nefarious.tasks.test',
#        'schedule': 60.0,
#        'args': (16, 16)
#    },
#}


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
