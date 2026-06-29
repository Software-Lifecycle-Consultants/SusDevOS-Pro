"""
Base Django settings for SusDevOS.
Environment-specific settings live in local.py (development) and production.py.
All secrets come from environment variables via python-decouple.
"""

from pathlib import Path
from decouple import config, Csv
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Security ──────────────────────────────────────────────────────────────────

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# ── Application definition ────────────────────────────────────────────────────

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",          # PostGIS support
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "django_celery_beat",
    "storages",
]

LOCAL_APPS = [
    "apps.shared",
    "apps.entities",
    "apps.users",
    "apps.projects",
    "apps.land",
    "apps.ecosystem",
    "apps.emissions",
    "apps.restorations",
    "apps.notifications",
    "apps.blog",
    "apps.reports",
    "apps.billing",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.entities.middleware.TenantQueryMiddleware",   # entity scoping — always last
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ── Database ──────────────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME":     config("DB_NAME",     default="susdevos"),
        "USER":     config("DB_USER",     default="susdevos"),
        "PASSWORD": config("DB_PASSWORD", default="susdevos"),
        "HOST":     config("DB_HOST",     default="localhost"),
        "PORT":     config("DB_PORT",     default="5432"),
        "CONN_MAX_AGE": 60,
    }
}

# ── Auth ──────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = "users.Users"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalisation ──────────────────────────────────────────────────────

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static and media files ────────────────────────────────────────────────────

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Django REST Framework ─────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.users.authentication.RevokedTokenJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.shared.exceptions.custom_exception_handler",
    # Base throttle rates (production.py overrides anon/user and adds production limits)
    "DEFAULT_THROTTLE_RATES": {
        "anon":        "60/min",   # production.py tightens this to 10/min
        "user":        "300/min",  # production.py tightens this to 100/min
        "public_read": "60/min",   # public blog/sitemap — permissive for crawlers
    },
}

# ── JWT ───────────────────────────────────────────────────────────────────────

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=config("JWT_ACCESS_MINUTES", default=15, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=config("JWT_REFRESH_DAYS", default=7, cast=int)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": config("JWT_SIGNING_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "USER_ID_FIELD": "UserId",
    "USER_ID_CLAIM": "user_id",
}

# ── drf-spectacular (OpenAPI) ─────────────────────────────────────────────────

SPECTACULAR_SETTINGS = {
    "TITLE": "SusDevOS API",
    "DESCRIPTION": (
        "GHG reporting, ecosystem tracking, and sustainable development platform. "
        "Aligned to GHG Protocol, IPCC, and TNFD."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    # Suppress enum generation to avoid duplicate schema names from shared choices
    "SCHEMA_COERCE_PATH_PK_SUFFIX": True,
    "ENUM_GENERATE_CHOICE_DESCRIPTION": False,
    "COMPONENT_SPLIT_PATCH": False,
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
    # Disable enum generation entirely — fields become integer/string in schema
    "GENERIC_ADDITIONAL_PROPERTIES": False,
    "DISABLE_ERRORS_AND_WARNINGS": False,
}

# ── CORS ──────────────────────────────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ── Celery ────────────────────────────────────────────────────────────────────

CELERY_BROKER_URL  = config("CELERY_BROKER_URL",  default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT  = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ── File storage (S3 / MinIO) ─────────────────────────────────────────────────

AWS_ACCESS_KEY_ID     = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="susdevos-dev")
AWS_S3_REGION_NAME    = config("AWS_S3_REGION_NAME", default="eu-west-2")
AWS_S3_ENDPOINT_URL   = config("AWS_S3_ENDPOINT_URL", default=None)  # set for MinIO
AWS_DEFAULT_ACL       = "private"
AWS_S3_FILE_OVERWRITE = False

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# ── Redis cache ───────────────────────────────────────────────────────────────

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://localhost:6379/2"),
    }
}

# ── External API keys ─────────────────────────────────────────────────────────

CLIMATIQ_API_KEY            = config("CLIMATIQ_API_KEY", default="")
COMPANIES_HOUSE_API_KEY     = config("COMPANIES_HOUSE_API_KEY", default="")
OPENCORPORATES_API_KEY      = config("OPENCORPORATES_API_KEY", default="")
OPEN_EXCHANGE_RATES_API_KEY = config("OPEN_EXCHANGE_RATES_API_KEY", default="")
IUCN_API_KEY                = config("IUCN_API_KEY", default="")
DEFRA_EF_SPREADSHEET_URL    = config("DEFRA_EF_SPREADSHEET_URL", default="")
VERRA_CSV_URL               = config("VERRA_CSV_URL", default="")
GOLD_STANDARD_API_URL       = config("GOLD_STANDARD_API_URL", default="")
EPA_EGRID_URL               = config("EPA_EGRID_URL", default="")

# ── GHG Protocol defaults ─────────────────────────────────────────────────────

DEFAULT_GWP_DATASET_ID = config("DEFAULT_GWP_DATASET_ID", default=1, cast=int)

# ── Site ──────────────────────────────────────────────────────────────────────

SITE_NAME = config("SITE_NAME", default="SusDevOS")
SITE_URL  = config("SITE_URL",  default="http://localhost:3000")

FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")
PASSWORD_RESET_URL = f"{FRONTEND_URL}/reset-password"
ONBOARDING_URL     = f"{FRONTEND_URL}/onboarding"

# ── Email ─────────────────────────────────────────────────────────────────────

EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST     = config("EMAIL_HOST", default="")
EMAIL_PORT     = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS  = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER     = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL  = config("DEFAULT_FROM_EMAIL", default="noreply@susdevos.com")

# ── Logging ───────────────────────────────────────────────────────────────────

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps":   {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "tasks":  {"handlers": ["console"], "level": "INFO",  "propagate": False},
    },
}
