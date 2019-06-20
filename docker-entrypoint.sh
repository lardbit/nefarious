#!/bin/sh

# build django database/tables
/env/bin/python manage.py migrate

# create default superuser
/env/bin/python manage.py nefarious-init ${NEFARIOUS_USER-admin} ${NEFARIOUS_EMAIL-admin@localhost} ${NEFARIOUS_PASS-admin}

# run app
/env/bin/gunicorn -w 2 -b 0.0.0.0:80 nefarious.wsgi