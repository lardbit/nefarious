#!/bin/sh

# setup
. $(dirname $0)/entrypoint-base.sh

# run celery worker/scheduler as requested user

# run celery worker & scheduler separately
if [ ! -z $CELERY_BEAT_SEPARATELY ]; then
  # run celery scheduler
  if [ ! -z $CELERY_BEAT ]; then
    su $(id -un ${RUN_AS_UID}) -c "/env/bin/celery -A nefarious beat --loglevel=INFO"
  # run celery workers with defined concurrency
  else
    su $(id -un ${RUN_AS_UID}) -c "/env/bin/celery -A nefarious worker --concurrency ${NUM_CELERY_WORKERS:-0} --loglevel=INFO"
  fi
# run celery worker & scheduler at the same time
# NOTE: this isn't advised since the scheduler could be potentially running multiple/simultaneous times creating duplicate tasks
else
  su $(id -un ${RUN_AS_UID}) -c "/env/bin/celery -A nefarious worker --concurrency ${NUM_CELERY_WORKERS:-0} --beat --pidfile= --loglevel=INFO"
fi
