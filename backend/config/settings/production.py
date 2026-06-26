"""
Production settings for SusDevOS.

Activated by: DJANGO_SETTINGS_MODULE=config.settings.production

All secrets must be set in environment variables -- never hardcode here.
"""
from .base import *  # noqa: F401, F403

# ── Security ──────────────────────────────────────────────────────────────────

DEBUG = False

# ALLOWED_HOSTS must be set explicitly in production
# e.g. ALLOWED_HOSTS=api.susdevos.com,susdevos.com
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())  # noqa: F405

SECRET_KEY = config("SECRET_KEY")  # noqa: F405  -- must be long random value

# HTTPS enforcement
SECURE_SSL_REDIRECT             = True
SECURE_HSTS_SECONDS             = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS  = True
SECURE_HSTS_PRELOAD             = True
SECURE_PROXY_SSL_HEADER         = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookies
SESSION_COOKIE_SECURE   = True
CSRF_COOKIE_SECURE      = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY    = True
SESSION_COOKIE_SAMESITE = "Lax"

# Content security
X_FRAME_OPTIONS          = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER   = True

# ── File storage (S3) ─────────────────────────────────────────────────────────

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# AWS_* values come from base.py (read from env); no local overrides needed.

# ── Email ─────────────────────────────────────────────────────────────────────

EMAIL_BACKEND = config(  # noqa: F405
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)

# ── Logging ───────────────────────────────────────────────────────────────────

try:
    import pythonjsonlogger  # noqa: F401  # type: ignore[import-untyped]
    _LOG_FORMATTER = "json"
    _LOG_FORMATTER_CONFIG = {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    }
except ImportError:
    _LOG_FORMATTER = "verbose"
    _LOG_FORMATTER_CONFIG = {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        }
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": _LOG_FORMATTER_CONFIG,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": _LOG_FORMATTER,
        },
    },
    "root":   {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django":      {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps":        {"handlers": ["console"], "level": "INFO",    "propagate": False},
        "tasks":       {"handlers": ["console"], "level": "INFO",    "propagate": False},
        "celery":      {"handlers": ["console"], "level": "INFO",    "propagate": False},
    },
}

# ── Django REST Framework (production hardening) ──────────────────────────────

REST_FRAMEWORK.update({  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",  # no Browsable API in production
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon":        config("RATE_LIMIT_UNAUTHENTICATED", default="10/min"),   # noqa: F405
        "user":        config("RATE_LIMIT_AUTHENTICATED",   default="100/min"),  # noqa: F405
        "public_read": config("RATE_LIMIT_PUBLIC_READ",     default="60/min"),   # noqa: F405 — crawlers + readers
    },
})

# ── Cache (Redis) ─────────────────────────────────────────────────────────────
# Override cache with longer timeouts in production (base.py sets 2-min stale time)

# ── CORS ──────────────────────────────────────────────────────────────────────
# CORS_ALLOWED_ORIGINS from base.py (env var) -- no override needed.
# Ensure CORS_ALLOW_ALL_ORIGINS is NOT set to True.
CORS_ALLOW_ALL_ORIGINS = False
