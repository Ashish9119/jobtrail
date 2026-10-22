#!/usr/bin/env bash
# Build step for the hosting platform: install, collect static files, migrate.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
