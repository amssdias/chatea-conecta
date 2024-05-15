from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

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
