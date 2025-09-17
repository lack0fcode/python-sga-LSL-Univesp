from .settings import *
import os

if os.environ.get("GITHUB_ACTIONS") == "true":
    # Use PostgreSQL in GitHub Actions
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'testdb'),
            'USER': os.environ.get('POSTGRES_USER', 'testuser'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'testpass'),
            'HOST': os.environ.get('POSTGRES_HOST', 'postgres'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }
else:
    # Use SQLite in-memory for local tests
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

LOGGING['loggers']['core.views']['level'] = 'WARNING'
