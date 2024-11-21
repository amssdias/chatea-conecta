"""
Django settings for chat_connect project.

Generated by 'django-admin startproject' using Django 4.2.11.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import sentry_sdk


load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "")

ALLOWED_HOSTS = []

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

MY_PROJECT_APPS = [
    "apps.chat",
    "apps.users"
]
EXTERNAL_APPS = [
    "daphne"
]

INSTALLED_APPS = MY_PROJECT_APPS + EXTERNAL_APPS + DJANGO_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  # Handles security headers like HTTPS redirection
    "django.contrib.sessions.middleware.SessionMiddleware",  # Manages user sessions
    "django.middleware.common.CommonMiddleware",  # Handles ETags, URL rewrites, etc.
    "django.middleware.csrf.CsrfViewMiddleware",  # Protects against Cross-Site Request Forgery
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Handles user authentication
    "django.contrib.messages.middleware.MessageMiddleware",  # Manages messages (e.g., success/error notices)
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # Prevents clickjacking attacks
]

ROOT_URLCONF = "chat_connect.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "chat_connect.wsgi.application"
ASGI_APPLICATION = "chat_connect.asgi.application"
AUTH_USER_MODEL = "users.User"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

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


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

# Enable localization
USE_L10N = True

USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("es", "Spanish"),
    ("pt", "Portuguese"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Where it will store when run collectstatic
STATIC_ROOT = BASE_DIR / "prod_static"


STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Redis
REDIS_PROTOCOL = os.getenv("REDIS_PROTOCOL", "rediss")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_URL = f"{REDIS_PROTOCOL}://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

# Django Cache
DJANGO_REDIS_CACHE_DB = os.getenv("DJANGO_REDIS_CACHE_DB", "0")
DJANGO_REDIS_KEY_PREFIX = "django-chat-app:"
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": DJANGO_REDIS_KEY_PREFIX,
        "OPTIONS": {
            "db": DJANGO_REDIS_CACHE_DB,
        },
    }
}
CACHE_MIDDLEWARE_SECONDS = 60 * 15  # Cache for 15 minutes


CACHE_TIMEOUT_FIVE_MIN = 300
CACHE_TIMEOUT_ONE_DAY = 86400
CACHE_TIMEOUT_ONE_WEEK = 604800
CACHE_TIMEOUT_ONE_MONTH = 2592000

# Web Socket - Channels
REDIS_DB_CHANNEL = os.getenv("REDIS_DB_CHANNEL")
REDIS_CHANNEL_LAYER_URL = f"{REDIS_URL}/{REDIS_DB_CHANNEL}"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_CHANNEL_LAYER_URL], "expiry": 60},
    },
}

# Celery settings
REDIS_DB_CELERY = os.getenv("REDIS_DB_CELERY")
CELERY_BROKER_URL = f"{REDIS_URL}/{REDIS_DB_CELERY}"
CELERY_REDIS_BACKEND_HEALTH_CHECK_INTERVAL = 60
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TIMEZONE = "UTC"

# Sentry configuration
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DNS"),
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)