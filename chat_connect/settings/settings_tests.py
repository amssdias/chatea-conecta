from chat_connect.settings.base import *

REDIS_PASSWORD = "redis-test"
REDIS_PORT = "6380"
REDIS_HOST = "my-redis-tests"
REDIS_CHANNEL_LAYER_URL = f"{REDIS_PROTOCOL}://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_CHANNEL_LAYER_URL],  # Reference the test Redis service
        },
    },
}
