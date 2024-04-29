from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_CHANNEL_LAYER_URL],
        },
    },
}

COOKIES_SECURE = True
