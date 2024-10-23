from chat_connect.settings.base import *
import secrets

SECRET_KEY = "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50))

# DB
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Web Socket - Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Use in-memory cache for testing (Django cache)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Use an in-memory broker URL if using Celery
CELERY_BROKER_URL = "memory://localhost"
COOKIES_SECURE = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "level": "DEBUG",
            "propagate": False,
        },
        "chat_connect": {
            "handlers": ["null"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

