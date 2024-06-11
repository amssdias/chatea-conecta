from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Used for auto reload CSS and HTML
INSTALLED_APPS += ["django_browser_reload"]
MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_CHANNEL_LAYER_URL],
        },
    },
}

# Cookies settings
COOKIES_SECURE = False
