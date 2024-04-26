from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Channels
ASGI_APPLICATION = "chat_connect.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

COOKIES_SECURE = True
