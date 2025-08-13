#!/bin/sh

PIPENV_DONT_LOAD_ENV=1
pipenv run python manage.py collectstatic -v 3 --clear --no-input --no-post-process
pipenv run python manage.py migrate
pipenv run gunicorn -c gunicorn.config.py saas_auth.wsgi --reload

# exec "$@"
