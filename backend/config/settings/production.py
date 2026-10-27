"""Production: DEBUG off, PostgreSQL via DATABASE_URL, hardened security flags."""

import dj_database_url

from .base import *
from .base import env
from .secrets import validate_secrets

DEBUG = False

# Refuse to start with placeholder/short secrets (e.g. values copied from .env.example).
validate_secrets(SECRET_KEY, HEALTH_CHECK_PASSWORD)

# Required in production: no SQLite fallback.
DATABASES = {"default": dj_database_url.parse(env("DATABASE_URL"), conn_max_age=600)}

# Shared cache for throttling across instances (separate Redis DB from Celery).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("RATELIMIT_CACHE_URL"),
    }
}

# API docs are hidden in production unless explicitly enabled.
API_DOCS_ENABLED = env.bool("API_DOCS_ENABLED", default=False)

# Security
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)  # set only behind a trusted proxy
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
REFRESH_COOKIE_SECURE = env.bool("REFRESH_COOKIE_SECURE", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
