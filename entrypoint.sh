#!/bin/sh

# build django database/tables
/env/bin/python manage.py migrate

# create default super user
/env/bin/python manage.py nefarious-init "${NEFARIOUS_USER-admin}" "${NEFARIOUS_EMAIL-admin@localhost}" "${NEFARIOUS_PASS-admin}"

# run app
authbind /env/bin/uvicorn --workers 2 --host 0.0.0.0 --port 80 nefarious.asgi:application