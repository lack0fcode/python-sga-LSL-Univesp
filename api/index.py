import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sga.settings")

# Import the WSGI application from the project's wsgi module
from sga.wsgi import application

# Export as 'app' for Vercel
app = application
