#!/bin/bash
python manage.py migrate
gunicorn sga.wsgi:application --bind 0.0.0.0:8080