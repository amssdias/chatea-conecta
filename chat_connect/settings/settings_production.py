from .base import *

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

MIDDLEWARE.insert(0, "django.middleware.cache.UpdateCacheMiddleware") # Save responses to cache (must come first)
MIDDLEWARE.insert(4, "django.middleware.cache.FetchFromCacheMiddleware") # Retrieve responses from cache (must be after CommonMiddleware)

# ====== Security for HTTPS Enforcement ======
# - SECURE_SSL_REDIRECT: Redirects all HTTP traffic to HTTPS, ensuring encrypted connections across the site.
# - SECURE_HSTS_SECONDS: Instructs browsers to remember to only connect to the site over HTTPS for the specified duration (1 year in seconds).
# - SECURE_HSTS_PRELOAD: Signals the site's readiness for inclusion in browser preload lists, enforcing HTTPS globally without needing an initial visit.
# - SECURE_HSTS_INCLUDE_SUBDOMAINS: Extends the HTTPS requirement to all subdomains, ensuring they also enforce HTTPS.
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ====== Cookie Security Settings ======
# - CSRF_COOKIE_SECURE: Ensures the CSRF cookie is only sent over HTTPS, protecting it from exposure over unencrypted connections.
# - SESSION_COOKIE_SECURE: Marks session cookies as HTTPS-only, preventing them from being sent over unsecured HTTP connections.
# - CSRF_TRUSTED_ORIGINS: Specifies trusted origins for cross-origin requests with CSRF protection.
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")

# ====== Header Security Settings ======
# - SECURE_BROWSER_XSS_FILTER: Enables the X-XSS-Protection header in compatible browsers to help prevent cross-site scripting (XSS) attacks.
# - SECURE_CONTENT_TYPE_NOSNIFF: Adds the X-Content-Type-Options header to prevent browsers from trying to guess the content type, reducing exposure to certain attack vectors.
# - X_FRAME_OPTIONS: Sets the X-Frame-Options header to "DENY", blocking the site from being embedded in iframes and protecting against clickjacking attacks.
# - SECURE_REFERRER_POLICY: Limits the referrer information sent in requests to the same origin only, reducing the potential for sensitive information leakage.
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# STATICFILES_STORAGE controls how Django handles static files during deployment.
# - It adds a unique hash to file names for cache-busting (e.g., main.css → main.abc123.css).
# - This ensures users always see the latest version of static files after updates.
# - Does NOT affect user-uploaded files (those are managed via MEDIA_ROOT/MEDIA_URL).
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_CHANNEL_LAYER_URL],
        },
    },
}

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

COOKIES_SECURE = True
