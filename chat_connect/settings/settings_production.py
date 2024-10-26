from .base import *

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")

# Django security settings
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = []
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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # Ensure other Django loggers remain active
    
    # Define the format of log messages
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },

    # Define where the log messages are sent
    "handlers": {
        "sentry": {
            "level": "WARNING",  # Log only warning and above
            "class": "sentry_sdk.integrations.logging.EventHandler",
            "formatter": "verbose",
        },
        # TODO: Config cloudwatch handler
        # "cloudwatch": {
        #     "level": "INFO",  # Log info and above to CloudWatch
        #     "class": "watchtower.CloudWatchLogHandler",
        #     "log_group": "your-log-group",  # Replace with your CloudWatch Log Group
        #     "stream_name": "django-app",  # Replace with your CloudWatch log stream name
        #     "formatter": "verbose",
        # },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },

    # Define the loggers themselves
    "loggers": {
        "django": {  # Django core logs
            "handlers": ["sentry"],  # Log to Sentry and CloudWatch
            "level": "WARNING",
            "propagate": True,
        },
        # "chat_connect": {
        #     "handlers": ["cloudwatch"],  # Log only to CloudWatch
        #     "level": "INFO",
        #     "propagate": False,
        # },
    },
}

# Time in minutes to expire messages sent
CLEAR_MESSAGES_EXPIRATION_TIME = 10
CLEAR_USER_SENT_MESSAGES_TASK_INTERVAL_SCHEDULE_MINUTES = 10

COOKIES_SECURE = True
