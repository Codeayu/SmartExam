#!/bin/bash
# Exit on error
set -o errexit

# Start Gunicorn
gunicorn smartexam.wsgi:application --bind 0.0.0.0:$PORT