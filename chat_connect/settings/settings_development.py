from .base import *

DEBUG = True
AUTH_PASSWORD_VALIDATORS = []

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "3306"),
    }
}

# Used for auto reload CSS and HTML
INSTALLED_APPS += ["django_browser_reload"]
MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]

# Cookies settings
COOKIES_SECURE = False

# CELERY
CELERY_TASK_ALWAYS_EAGER = False # If true must disable task on chat consumer
CELERY_TASK_EAGER_PROPAGATES = True

# Time in minutes to expire messages sent
CLEAR_MESSAGES_EXPIRATION_TIME = 10

CACHE_TIMEOUT_ONE_DAY = 120
CACHE_TIMEOUT_ONE_WEEK = 120
CACHE_TIMEOUT_ONE_MONTH = 120

LOGGING = {
    "version": 1,  # Version of the logging configuration (always 1)
    "disable_existing_loggers": False,  # Ensures that Django’s default loggers are not disabled

    # Define the format of log messages
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },

    # Define where the log messages are sent
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",  # Use the "verbose" formatter for console logs
        },
    },

    # Define the loggers themselves
    "loggers": {
        "chat_connect": {
            "handlers": ["console"],  # Send logs to console
            "level": "INFO",  # Log everything, including info messages
            "propagate": False,
        },
    },
}
