#!/bin/sh

# setup
. $(dirname $0)/entrypoint-base.sh

# run as requested user
su $(id -un ${RUN_AS_UID}) -c "/env/bin/celery -A nefarious worker --concurrency ${NUM_CELERY_WORKERS:-0} --beat --loglevel=INFO"
