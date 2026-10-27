"""Shared settings. Every environment-specific value comes from the environment."""

from datetime import timedelta
from pathlib import Path

import dj_database_url
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Load .env if present (never committed). Real environment variables win.
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env("SECRET_KEY", default="")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "common",
    "apps.core",
    "apps.users",
    "apps.locations",
    "apps.shops",
    "apps.orders",
    "apps.audit",
    "apps.notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "common.middleware.NoStoreMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.middleware.AdminLoginThrottleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("username", "full_name", "phone", "email")},
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("ar", "Arabic")]
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = True
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = env("STATIC_PATH", default=str(BASE_DIR / "staticfiles"))
MEDIA_URL = "media/"
MEDIA_ROOT = env("MEDIA_PATH", default=str(BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

# CORS. Credentials are required so the browser will store and send the
# HttpOnly refresh cookie (VULN-012). Origins stay an explicit list, never "*".
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
# Secure flag on the refresh cookie. Off in local HTTP dev; production overrides.
REFRESH_COOKIE_SECURE = env.bool("REFRESH_COOKIE_SECURE", default=False)

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.users.authentication.StatusCheckingJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    # JSON only: no browsable/HTML API (VULN-004).
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "common.parsers.SafeJSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "EXCEPTION_HANDLER": "common.exception_handler.exception_handler",
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    # Number of trusted reverse proxies (0 = use REMOTE_ADDR only). Without this DRF trusts a
    # client-supplied X-Forwarded-For, which lets anyone dodge throttling (VULN-001).
    "NUM_PROXIES": env.int("NUM_PROXIES", default=0),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("RATELIMIT_ANON", default="60/minute"),
        "user": env("RATELIMIT_USER", default="300/minute"),
        "auth": env("RATELIMIT_AUTH", default="10/minute"),
        "sensitive": env("RATELIMIT_SENSITIVE", default="30/minute"),
        "health": env("RATELIMIT_HEALTH", default="120/minute"),
        # Password recovery: per IP, and per normalised identifier (TASK-048).
        "recovery": env("RATELIMIT_RECOVERY", default="5/hour"),
        "recovery_identifier": env("RATELIMIT_RECOVERY_IDENTIFIER", default="5/hour"),
    },
}

# Password recovery (TASK-048). The email link points at the frontend.
FRONTEND_ORIGIN = env("FRONTEND_ORIGIN", default="http://localhost:5173").rstrip("/")
PASSWORD_RESET_TIMEOUT_MINUTES = env.int("PASSWORD_RESET_TIMEOUT_MINUTES", default=30)
# Console mail in development; production sets EMAIL_BACKEND and the SMTP values.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Delivery <no-reply@localhost>")

API_PAGE_SIZE = env.int("API_PAGE_SIZE", default=20)

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)
    ),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Admin login brute-force protection (common.middleware.AdminLoginThrottleMiddleware)
ADMIN_LOGIN_MAX_ATTEMPTS = env.int(
    "ADMIN_LOGIN_MAX_ATTEMPTS", default=5
)  # failures per IP
ADMIN_LOGIN_MAX_ATTEMPTS_PER_USERNAME = env.int(
    "ADMIN_LOGIN_MAX_ATTEMPTS_PER_USERNAME", default=30
)
ADMIN_LOGIN_WINDOW_SECONDS = env.int("ADMIN_LOGIN_WINDOW_SECONDS", default=900)

# OpenAPI docs endpoints (production overrides the default to False)
API_DOCS_ENABLED = env.bool("API_DOCS_ENABLED", default=True)

# OpenAPI
SPECTACULAR_SETTINGS = {
    "TITLE": "Delivery API",
    "DESCRIPTION": "Delivery platform backend API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# After logging in through /admin/login/ (the form has no `next` field) go to the admin, not /accounts/profile/.
LOGIN_URL = "admin:login"
LOGIN_REDIRECT_URL = "admin:index"

# Admin (Jazzmin)
JAZZMIN_SETTINGS = {
    "site_title": "Delivery Admin",
    "site_header": "Delivery Administration",
    "site_brand": "Delivery",
    "welcome_sign": "Welcome to the administration panel",
    "copyright": "Delivery",
    "show_sidebar": True,
    "navigation_expanded": True,
}

# Health API
HEALTH_CHECK_PASSWORD = env("HEALTH_CHECK_PASSWORD", default="")

# Celery (off unless a settings module / env enables it; no Redis needed when off)
CELERY_ENABLED = env.bool("CELERY_ENABLED", default=False)
CELERY_BEAT_ENABLED = env.bool("CELERY_BEAT_ENABLED", default=False)
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = env.bool("CELERY_TASK_EAGER_PROPAGATES", default=False)
CELERY_WORKER_CONCURRENCY = env.int("CELERY_WORKER_CONCURRENCY", default=2)

# Default cache: local memory (overridden by Redis in staging/production)
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# CORS: allow the health token header from the frontend origin
from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = (*default_headers, "x-health-check-token")
