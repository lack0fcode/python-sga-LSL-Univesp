import os

from ..settings import *

# Decide which DB to use for tests.
# Prefer an explicit CI flag `CI_USE_SQLITE`. If set to 'true', use SQLite.
# Otherwise, if Postgres connection env vars are present, prefer Postgres.
# Fall back to SQLite in-memory.
ci_use_sqlite = os.environ.get("CI_USE_SQLITE")
postgres_host = os.environ.get("POSTGRES_HOST") or os.environ.get("POSTGRES_SERVICE_HOST")

if ci_use_sqlite and ci_use_sqlite.lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
elif os.environ.get("POSTGRES_DB") or os.environ.get("POSTGRES_USER") or postgres_host:
    # Use PostgreSQL when explicit Postgres env vars are provided
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "testdb"),
            "USER": os.environ.get("POSTGRES_USER", "testuser"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "testpass"),
            "HOST": os.environ.get("POSTGRES_HOST", postgres_host or "postgres"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    # Default to SQLite in-memory for local developer runs
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# print("USANDO BANCO:", DATABASES["default"]["ENGINE"])

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LOGGING["loggers"]["core.views"] = {"level": "CRITICAL", "handlers": []}  # type: ignore

LOGGING["handlers"]["console"] = {"class": "logging.NullHandler"}

LOGGING["root"] = {"handlers": [], "level": "CRITICAL"}  # type: ignore

LOGGING["disable_existing_loggers"] = True
