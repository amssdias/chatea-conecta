from chat_connect.settings.base import *


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
