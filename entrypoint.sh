#!/bin/sh

# setup
. $(dirname $0)/entrypoint-base.sh

# build django database/tables
su $(id -un ${RUN_AS_UID:-1000}) -c "/env/bin/python manage.py migrate"

# initialization script arguments (default nefarious user)
INIT_ARGS="\
--username ${NEFARIOUS_USER:-admin} \
--password ${NEFARIOUS_PASS:-admin} \
--email ${NEFARIOUS_EMAIL:-admin@localhost} \
"

# append transmission credentials if they exist
if [ ! -z ${TRANSMISSION_USER} ] && [ ! -z ${TRANSMISSION_PASS} ]; then
  INIT_ARGS="${INIT_ARGS} \
    --transmission_user ${TRANSMISSION_USER-admin} \
    --transmission_pass ${TRANSMISSION_PASS-admin} \
  "
fi

# run initialization script
su $(id -un ${RUN_AS_UID:-1000}) -c "/env/bin/python manage.py nefarious-init ${INIT_ARGS}"

# allow user to bind to port 80
touch /etc/authbind/byport/80
chmod 500 /etc/authbind/byport/80
chown ${RUN_AS_UID:-1000} /etc/authbind/byport/80

# run as requested user
su $(id -un ${RUN_AS_UID:-1000}) -c "authbind /env/bin/uvicorn --workers 2 --host 0.0.0.0 --port 80 nefarious.asgi:application"
