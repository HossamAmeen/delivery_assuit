"""Staging (server only): production-like, with Celery + Redis cache/throttling enabled."""

from .production import *
from .production import env

# PO decision 2026-10-08: Celery and Redis are enabled on the server (staging) only.
CELERY_ENABLED = True
CELERY_BEAT_ENABLED = env.bool("CELERY_BEAT_ENABLED", default=True)
CELERY_TASK_ALWAYS_EAGER = False

# Redis: DB 0 broker, DB 1 results, DB 2 cache/throttling (see .env.example).
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")

# Staging may sit behind plain HTTP until TLS is set up; override via env.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
