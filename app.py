import os
import sys

# Add the project directory to the sys.path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartexam.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()

# This allows Render to find the application when running 'gunicorn app:app'
if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)