"""Local development: SQLite by default, no Redis, no Celery."""

from .base import *
from .base import env

# Non-secret fallback so tests/CI run without a .env; real .env value wins.
SECRET_KEY = env("SECRET_KEY", default="insecure-development-only-key")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Celery and Redis are intentionally disabled locally (PO decision 2026-10-08).
CELERY_ENABLED = False
CELERY_BEAT_ENABLED = False
CELERY_TASK_ALWAYS_EAGER = True

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173", "http://127.0.0.1:5173"]
)

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
