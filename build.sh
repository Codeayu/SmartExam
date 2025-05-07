#!/bin/bash
# Exit on error
set -o errexit

# Install pip packages
pip install -r requirements.txt

# Run collectstatic
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate