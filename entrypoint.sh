#!/bin/sh

# setup
. $(dirname $0)/entrypoint-base.sh

# build django database/tables
su $(id -un ${RUN_AS_UID}) -c "/env/bin/python manage.py migrate"

# create default super user
su $(id -un ${RUN_AS_UID}) -c "/env/bin/python manage.py nefarious-init ${NEFARIOUS_USER-admin} ${NEFARIOUS_EMAIL-admin@localhost} ${NEFARIOUS_PASS-admin}"

# allow user to bind to port 80
touch /etc/authbind/byport/80
chmod 500 /etc/authbind/byport/80
chown ${RUN_AS_UID} /etc/authbind/byport/80

# run as requested user
su $(id -un ${RUN_AS_UID}) -c "authbind /env/bin/uvicorn --workers 2 --host 0.0.0.0 --port 80 nefarious.asgi:application"
