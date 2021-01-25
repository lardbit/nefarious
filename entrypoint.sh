#!/bin/sh

# TODO - eventually run as non-root user, but give enough time for users to run these file permission updates

RUN_AS_USER=nonroot
CONFIG_PATH=/nefarious-db/

# set config path permissions to be writable by the non-root user
if [ -e "${CONFIG_PATH}" ]
  then
    chown -R $RUN_AS_USER:$RUN_AS_USER "${CONFIG_PATH}"
  else
    echo config path ${CONFIG_PATH} does not exist so cannot set permissions
fi

# build django database/tables
/env/bin/python manage.py migrate

# create default super user
/env/bin/python manage.py nefarious-init "${NEFARIOUS_USER-admin}" "${NEFARIOUS_EMAIL-admin@localhost}" "${NEFARIOUS_PASS-admin}"

# run app
/env/bin/uvicorn --workers 2 --host 0.0.0.0 --port 80 nefarious.asgi:application
