#!/bin/sh

RUN_AS_USER=nonroot
CONFIG_PATH=/nefarious-db/

# set config path permissions to be writable by the non-root user
if [ -e "${CONFIG_PATH}" ]
  then
    chown -R $RUN_AS_USER:$RUN_AS_USER"${CONFIG_PATH}"
  else
    echo config path ${CONFIG_PATH} does not exist so cannot set permissions
fi

su ${RUN_AS_USER} -c "/env/bin/celery -A nefarious worker --concurrency ${NUM_CELERY_WORKERS:-0} --beat --loglevel=INFO"
