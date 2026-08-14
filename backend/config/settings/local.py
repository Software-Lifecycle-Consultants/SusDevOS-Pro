"""
Local development settings.
Overrides base.py for the dev environment.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

# Use console email backend in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Use local filesystem for file storage instead of S3
# (DEFAULT_FILE_STORAGE kept as the flag tasks/reports.py reads; STORAGES is
# what Django 5.1 core reads.)
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Django Debug Toolbar (install separately: pip install django-debug-toolbar)
try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass

# Relax CORS in development
CORS_ALLOW_ALL_ORIGINS = True
