#!/usr/bin/env bash
set -e

echo "Running migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2
