#!/bin/sh

RUN_AS_USER=nonroot

# build django database/tables
su ${RUN_AS_USER} -c "/env/bin/python manage.py migrate"

# create default super user
su ${RUN_AS_USER} -c "/env/bin/python manage.py nefarious-init ${NEFARIOUS_USER-admin} ${NEFARIOUS_EMAIL-admin@localhost} ${NEFARIOUS_PASS-admin}"

# run app
su ${RUN_AS_USER} -c "authbind /env/bin/uvicorn --workers 2 --host 0.0.0.0 --port 80 nefarious.asgi:application"
