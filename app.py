"""
Entry point for Render deployment
This file provides the app object that Render looks for by default
"""

from smartexam.wsgi import application as app

# This makes the app available at the module level with the name Render expects
# When Render runs 'gunicorn app:app', it will find this variable