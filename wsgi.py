"""
WSGI entry point for Render deployment
This file provides a direct entry point for Render which looks for app.py or wsgi.py by default
"""

from smartexam.wsgi import application as app

# Make the application available at the module level as Render expects
application = app