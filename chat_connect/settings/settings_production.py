from .base import *

DEBUG = False
ALLOWED_HOSTS = []

# Django security settings
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 300  # 1 year after testing
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"


# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_CHANNEL_LAYER_URL],
        },
    },
}

# Time in minutes to expire messages sent
CLEAR_MESSAGES_EXPIRATION_TIME = 10
CLEAR_USER_SENT_MESSAGES_TASK_INTERVAL_SCHEDULE_MINUTES = 10

COOKIES_SECURE = True
