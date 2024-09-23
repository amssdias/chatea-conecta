from .base import *

DEBUG = True
AUTH_PASSWORD_VALIDATORS = []

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = []

# Used for auto reload CSS and HTML
INSTALLED_APPS += ["django_browser_reload"]
MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]

# Cookies settings
COOKIES_SECURE = False

# CELERY
CELERY_TASK_ALWAYS_EAGER = False # If true must disable task on chat consumer
CELERY_TASK_EAGER_PROPAGATES = True
