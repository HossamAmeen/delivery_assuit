# TASK-002: Backend settings split, env config, requirements, pytest and Makefile

- **Backlog item:** BL-001
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-001
- **Estimate:** M

## Description
Create the `backend/` project foundation following the drf-backend skill (CREATE mode, sections 3, 7-9, 34-37, 45, 57).

## Technical Notes
- Structure: `backend/{manage.py, config/{settings/{__init__,base,development,production}.py, urls.py, asgi.py, wsgi.py}, apps/, common/, tests/, requirements/{base,development,production}.txt, scripts/, Makefile, pytest.ini, .env.example, .gitignore, README.md}`. Python 3.13+.
- Settings: `base.py` (shared), `development.py` (SQLite default), `production.py` (security flags, PostgreSQL). Never a single settings file.
- Config via `django-environ` (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL` via `dj_database_url`, JWT lifetimes, `HEALTH_CHECK_PASSWORD`, `RATELIMIT_*`, `CELERY_ENABLED=False`, CORS origins). No secrets committed; `.env` git-ignored; `.env.example` only with placeholders.
- Requirements: django, djangorestframework, django-environ, dj-database-url, djangorestframework-simplejwt, drf-spectacular, django-jazzmin, django-cors-headers, django-filter, psycopg (prod), pytest, pytest-django, pytest-cov, factory_boy, ruff.
- `pytest.ini` per skill (`DJANGO_SETTINGS_MODULE=config.settings.development`). One sample test (e.g. `tests/test_smoke.py`) passes.
- Makefile targets: install, install-dev, run, migrate, makemigrations, test (also runs rate-limit tests), coverage, check, lint (`ruff check .`), format (`ruff format .`), shell, collectstatic, test-rate-limit (`pytest -k "throttle or rate_limit"`).
- Celery/Redis: OFF in development settings (`CELERY_ENABLED=False`, local-memory cache, no worker/Beat). ON in staging/server only (PO decision 2026-10-08): add `config/settings/staging.py` with Celery + Redis cache/throttling enabled and Redis/worker/beat in the staging compose file (written, not run). Production settings stay env-driven.
- README section: how to run the backend and its tests.

## Acceptance Criteria
- [x] `make run` starts the server locally with only a `.env` copied from `.env.example`
- [x] No secret, DB credential or password hardcoded; settings read from environment
- [x] `make test` runs one command and the sample test passes
- [x] `python manage.py check` and `makemigrations --check` pass; `ruff check .` clean
- [x] README has backend run + test instructions
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-08 — backend: Implemented backend/ foundation (settings base/development/staging/production, env config + .env.example, requirements, pytest.ini, Makefile, README, smoke tests). Dev: SQLite, no Redis/Celery; staging: Celery + Redis. check, makemigrations --check, ruff, pytest (3 passed) green on Python 3.12 (3.13 not installed locally). Docker staging compose NOT written (Docker not run; left to DevOps). Status -> IN_REVIEW.
- 2026-10-10 — qa: TASK-021 backend QA PASS (see QA_REPORT.md); status DONE.
