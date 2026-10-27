---
name: drf-backend
description: Standard architecture, workflow, testing, Docker, deployment, and rules for Django REST Framework backends. Use when creating a new DRF project, refactoring an existing Django/DRF project, or adding/modifying backend features (models, APIs, auth, throttling, health checks, Celery, Docker, Nginx/systemd deployment).
---

# Django REST Framework Engineering Skill

Domain-agnostic standard for DRF backends (SaaS, delivery, healthcare, e-commerce, ERP, CRM, booking, fintech, internal apps, microservices).

Modes:
- **CREATE** — new DRF project.
- **REFACTOR** — refactor an existing Django/DRF project.
- **UPDATE** — add or modify functionality in an existing project.

## 1. Engineering Principles

The agent MUST:
- Read and understand the project before making changes.
- Keep business domains separated into Django apps; shared infrastructure in `common/`.
- Keep business logic in the backend; use env vars for configuration and secrets.
- Use automated tests for business behavior.
- Preserve existing behavior when refactoring unless told otherwise; avoid unnecessary rewrites; prefer incremental, testable changes.
- Maintain backward compatibility and consistent API contracts.
- Use Django migrations for all schema changes.
- Never hardcode secrets, domains, ports, filesystem paths, or service names.
- Treat deployment configuration as code; validate before declaring work complete.

The backend is the source of truth for business rules, validation, authorization, state transitions, data integrity, security, calculations, and lifecycle rules. Frontends must not duplicate them.

## 2. Technology Stack

Required: Python 3.13+, Django, DRF, django-environ, dj-database-url, djangorestframework-simplejwt, drf-spectacular, django-jazzmin, pytest, pytest-django, pytest-cov, Docker, Docker Compose.

Database: SQLite locally; PostgreSQL for staging and production.

Optional: Redis, Celery, Celery Beat, Nginx, systemd. Celery/Redis are controlled by environment config.

## 3. Standard Project Structure

```
backend/
├── manage.py
├── config/
│   ├── __init__.py          # exports celery_app
│   ├── celery.py
│   ├── settings/{__init__,base,development,production}.py
│   ├── urls.py, asgi.py, wsgi.py
├── apps/
│   ├── __init__.py
│   ├── users/
│   │   ├── admin.py apps.py models.py managers.py serializers.py
│   │   ├── views.py urls.py permissions.py services.py selectors.py tasks.py
│   │   ├── tests/{__init__,conftest,test_models,test_serializers,test_views,test_services,test_tasks}.py
│   │   └── migrations/
│   └── <domain_apps>/
├── common/
│   ├── models.py managers.py exceptions.py exception_handler.py
│   ├── responses.py pagination.py permissions.py throttling.py
├── tests/{__init__,conftest}.py
├── requirements/{base,development,production}.txt
├── docker/{local,staging,production}/{Dockerfile,docker-compose.yml}
├── deploy/
│   ├── nginx/{generate.sh, templates/nginx.conf.template}
│   ├── systemd/templates/backend.service.template
│   └── scripts/{deploy,migrate,collectstatic,restart,healthcheck}.sh
├── scripts/{entrypoint,wait_for_db}.sh
├── .env  .env.example  .gitignore  Makefile  pytest.ini  README.md
```

Adapt for existing projects. Do not force a large refactor just to match this structure if the existing architecture is valid.

## 4. CREATE Mode

Order: Requirements → Project structure → Settings → Environment config → Database → DRF → JWT → Common infrastructure → OpenAPI → Jazzmin → Health API → Testing → Docker → Celery/Redis (if enabled) → Deployment structure → Domain apps → Business features → Validation.

Establish the foundation before implementing business features.

## 5. REFACTOR Mode

Do NOT rewrite immediately. First inspect: structure, settings, requirements, models, managers, views/viewsets, serializers, URLs, permissions, auth, services, selectors, tasks, tests, migrations, env config, Docker/Compose, Nginx, systemd, deploy scripts, API docs, Celery config.

Then identify: current architecture, problems, technical debt, security risks, testing gaps, deployment problems, performance problems, potential breaking changes, recommended order.

Recommended order: 1 env config, 2 settings separation, 3 common infra, 4 auth, 5 exception handling, 6 response standardization, 7 base model, 8 soft delete/managers, 9 domain separation, 10 services/selectors, 11 testing, 12 OpenAPI, 13 Docker, 14 deployment, 15 performance.

Never perform a large rewrite without a clear reason.

## 6. UPDATE Mode

Read → Understand → Identify affected domain → Inspect existing implementation → Inspect tests → Implement → Add/update tests → Update OpenAPI → Run validation. Do not modify unrelated functionality.

## 7. Settings

Split into `config/settings/base.py` (installed apps, middleware, DRF, auth, JWT, OpenAPI, Jazzmin, i18n, static/media, shared security, Celery), `development.py` (local), `production.py` (production). Never one settings file.

## 8. Environment Variables

Use `.env` locally. Commit only `.env.example`; never commit `.env`.

```
# Django
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=30
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Health API
HEALTH_CHECK_PASSWORD=change-me

# Celery
CELERY_ENABLED=False
CELERY_BEAT_ENABLED=False
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_ALWAYS_EAGER=False
CELERY_TASK_EAGER_PROPAGATES=False
CELERY_WORKER_CONCURRENCY=2

# Deployment
DOMAIN=example.com
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_PATH=/opt/myapp/backend
FRONTEND_PATH=/opt/myapp/frontend
MEDIA_PATH=/opt/myapp/backend/media
STATIC_PATH=/opt/myapp/backend/static
SYSTEMD_SERVICE_NAME=myapp-backend

# API Rate Limiting
RATELIMIT_ANON=60/minute
RATELIMIT_USER=300/minute
RATELIMIT_AUTH=10/minute
RATELIMIT_SENSITIVE=30/minute
RATELIMIT_HEALTH=120/minute

# Rate Limit Cache
RATELIMIT_CACHE_URL=redis://localhost:6379/2
```

Never hardcode passwords, secret keys, DB credentials, API keys, JWT secrets, domains, ports, filesystem paths, or systemd service names.

## 9. Database

```python
import dj_database_url

DATABASES = {
    "default": dj_database_url.config(default="sqlite:///db.sqlite3", conn_max_age=600)
}
```

SQLite locally; PostgreSQL in staging/production. All schema changes via migrations.

## 10. Common Package

Use `common/` (not `utils/`) for shared architectural infrastructure: models, managers, exceptions, exception_handler, responses, pagination, permissions, throttling. Only functionality shared across multiple apps belongs here; domain-specific code stays in its app.

## 11. Base Model (`common/models.py`)

```python
from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
```

## 12. Soft Delete

Set `deleted_at = now` instead of physically deleting. Provide `soft_delete()` and `restore()` where appropriate.

## 13. Custom Managers (`common/managers.py`)

```python
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class DeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=False)

class AllManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

class Example(BaseModel):
    objects = ActiveManager()
    deleted_objects = DeletedManager()
    all_objects = AllManager()
```

The default manager returns only active records.

## 14. Django Applications

One app per business domain (e.g. users, orders, products, payments, notifications). Never one giant app.

## 15. DRF API Architecture

All APIs use DRF. Each API has the appropriate serializer, view/viewset, URL, permission, validation, tests. Use the simplest appropriate DRF abstraction.

## 16. Business Logic

Layers: `models.py`, `services.py` (business workflows), `selectors.py` (complex reads). Do not duplicate business logic in web/PWA/Flutter/mobile clients.

## 17. Authentication

`djangorestframework-simplejwt` with access + refresh tokens: `POST /api/auth/token/`, `POST /api/auth/token/refresh/`. Lifetimes from env.

## 18. Authorization

DRF permissions: `IsAuthenticated`, `IsAdminUser`, custom role permissions, object-level permissions. Never rely on frontend permissions for security.

## 19. Standard API Responses

Success:
```json
{"success": true, "message": "Operation completed successfully.", "data": {}}
```
Error:
```json
{"success": false, "message": "Validation failed.", "errors": {"field": ["This field is required."]}}
```
In an existing project, do not change an established response contract unnecessarily.

## 20. Centralized Exception Handling

Implement `common/exception_handler.py` handling validation, authentication, permission, not found, throttling, custom application exceptions, and unexpected exceptions. All errors follow the standard structure. Do not duplicate formatting in views.

## 21. OpenAPI

`drf-spectacular`: `/api/schema/`, `/api/docs/`, `/api/redoc/`. Document every public API: request body, response, auth, query/path params, important validation rules.

## 22. Django Jazzmin

Install `django-jazzmin`; put `"jazzmin"` before `django.contrib.admin` in `INSTALLED_APPS`.

```python
JAZZMIN_SETTINGS = {
    "site_title": "Django Admin",
    "site_header": "Django Administration",
    "site_brand": "Backend",
    "welcome_sign": "Welcome to the administration panel",
    "copyright": "Backend",
    "show_sidebar": True,
    "navigation_expanded": True,
}
```

Not coupled to a business domain. Admin stays protected by Django auth and staff/superuser permissions.

## 23–27. Health API

- Every new project provides `GET /api/health/`.
- Password from env: `HEALTH_CHECK_PASSWORD = env("HEALTH_CHECK_PASSWORD")`. Never hardcode. Never expose it in responses or logs.
- Request: `GET /api/health/?password=<...>`. In production prefer header `X-Health-Check-Token` (query params appear in access logs).
- Success: `{"success": true, "message": "Service is healthy.", "data": {"status": "healthy"}}`
- Invalid: `{"success": false, "message": "Invalid health check password.", "errors": {}}`
- Never expose env vars, passwords, DB credentials, secret keys, stack traces, filesystem paths, internal exceptions.
- Basic health only verifies Django is running and must NOT depend on optional services. Optional `GET /api/health/ready/` may check DB, Redis, Celery, required external services. If `CELERY_ENABLED=False`, readiness must not require Celery.
- Required tests: `test_health_endpoint_returns_success_with_valid_password`, `test_health_endpoint_rejects_invalid_password`, `test_health_endpoint_requires_password`, `test_health_endpoint_does_not_expose_secret`. Readiness tests cover dependency failures. Use test env values, never production secrets.

## 28–33. Celery (optional)

- Must support `CELERY_ENABLED=False` and `True` without changing business code.
- Disabled: Django starts normally, Redis not required, no workers, no Beat. Enabled: broker available, workers deployed; Beat only when `CELERY_BEAT_ENABLED`.
- `config/celery.py`:
```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```
- `config/__init__.py`: `from .celery import app as celery_app; __all__ = ("celery_app",)`.
- Tasks live in the owning app's `tasks.py` and are thin wrappers: Task → Service → Business Logic → DB. No large workflows in tasks.
- If a task depends on data created in a transaction: `transaction.on_commit(lambda: task.delay(obj.id))`.
- External-system tasks: consider retries, backoff, max retries, failure handling, idempotency. Don't blindly retry non-idempotent operations.
- Docker: provide `redis`, `celery-worker`; `celery-beat` only when Beat enabled. Don't start them when disabled.

## 34–37. Testing

Use pytest, pytest-django, pytest-cov. Every business feature has automated tests covering:
- Models: creation, modification, soft delete, restore, managers, constraints, methods.
- Serializers: valid/invalid input, required fields, validation, representation.
- APIs: authentication, authorization, success, validation errors, not found, permissions, pagination, filtering.
- Services: happy paths, business rules, failures, edge cases, transactions.
- Celery: execution, arguments, success, failure, retry, idempotency.

Fixtures: global in `tests/conftest.py`, per-app in `apps/<app>/tests/conftest.py` (users, API clients, auth, domain objects, roles, permissions, common data). Don't duplicate setup.

Coverage: `pytest --cov=. --cov-report=term-missing`; minimum 80% initially, meaningful tests only.

`pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests.py test_*.py *_tests.py
addopts = --strict-markers
```

## 38. Migrations

`python manage.py makemigrations`, `migrate`, and validate with `makemigrations --check`. Never destructively modify migration history in an established project without explicit approval.

## 39–40. Performance & Pagination

Avoid N+1 (`select_related`, `prefetch_related`) where appropriate; don't optimize prematurely. Paginate collection APIs; never expose unbounded querysets publicly.

## 41–44. Docker

Separate per environment: `docker/{local,staging,production}/{Dockerfile,docker-compose.yml}`.
- Local: optimize DX; may include backend, database, redis, celery-worker, celery-beat; SQLite OK.
- Staging: resemble production; backend, postgres, redis, celery-worker, celery-beat, nginx (only what's required); isolated from production.
- Production: same set, or managed infrastructure instead. Don't force Docker for managed services.

## 45. Makefile

Every new project has a Makefile with: `install`, `install-dev`, `run`, `migrate`, `makemigrations`, `test`, `coverage`, `check`, `lint` (`ruff check .`), `format` (`ruff format .`), `shell`, `collectstatic`, `celery-worker`, `celery-beat`, `docker-local`, `docker-staging`, `docker-production`, `deploy-staging`, `deploy-production`, `test-rate-limit` (`pytest -k "throttle or rate_limit"`). `make test` must also run rate-limit tests. Project-specific commands may be added.

## 46–52. Deployment

Structure: `deploy/nginx/{generate.sh,templates/nginx.conf.template}`, `deploy/systemd/templates/backend.service.template`, `deploy/scripts/{deploy,migrate,collectstatic,restart,healthcheck}.sh`.

- Deployment reads `.env`: DOMAIN, BACKEND_PORT, FRONTEND_PORT, BACKEND_PATH, FRONTEND_PATH, MEDIA_PATH, STATIC_PATH, SYSTEMD_SERVICE_NAME, HEALTH_CHECK_PASSWORD. Never hardcode them in scripts.
- Nginx: template + generator reading env (DOMAIN, BACKEND_PORT, FRONTEND_PORT, BACKEND_PATH, FRONTEND_PATH, MEDIA_PATH, STATIC_PATH). Proxy `/api/` to `127.0.0.1:${BACKEND_PORT}`, alias `/media/` and `/static/`, serve frontend with `try_files $uri $uri/ /index.html`. Adapt to the actual project.
- systemd template uses `${SYSTEMD_SERVICE_NAME}`, `${BACKEND_PATH}`, `${BACKEND_PORT}`; Gunicorn/Uvicorn as appropriate; `Restart=always`.
- Deploy flow: load env → validate required vars → build/pull → install deps → migrate → collectstatic → generate Nginx config → generate/update systemd → restart backend → start required Celery services → health check. Use `set -euo pipefail`; never expose secrets in logs.
- Post-deploy health check (reads DOMAIN, HEALTH_CHECK_PASSWORD, BACKEND_PORT) must fail the deployment if unhealthy; never print the password.
- Docker healthchecks may call `/api/health/` with a secure mechanism; don't expose health credentials unnecessarily.

## 53–54. Environment Separation & Security

Clearly separate local/staging/production (Docker dirs and Django settings). Never deploy staging config to production; never use production credentials locally. Never hardcode secrets, domains, production paths, or service names. Don't expose or log `.env` / sensitive vars. Keep Django Admin protected.

## 55. Backward Compatibility

Preserve API contracts, data, auth behavior, business behavior. Avoid unnecessary renames, endpoint removal, destructive migrations. Clearly identify breaking changes.

## 56. API Contract

For significant features: Requirement → Domain analysis → Data model → API contract → Serializer → Service → View → Permission → Tests → OpenAPI. Define the contract before dependent frontend clients are built.

## 57. Required Validation Commands

Before completing work:
```
python manage.py check
python manage.py makemigrations --check
pytest
pytest --cov=. --cov-report=term-missing
ruff check .                       # if configured
docker compose -f docker/local/docker-compose.yml config   # Docker changes (also staging/production if changed)
```
Deployment changes: validate generated Nginx and systemd config, required env vars, and run deployment health checks.

## 58. Definition of Done

Requirement understood; correct app identified; model + migration; serializer; business logic; view/viewset; URL; permission; validation; standard response and exception handling verified; tests + fixtures; coverage checked; OpenAPI updated; existing tests pass; `check` and migration checks pass; Docker/Celery/Nginx/systemd/deploy scripts validated if changed; Jazzmin configured if applicable; Health API implemented; no hardcoded secrets or environment-specific values.

## 59. Existing Project Safety Rules

Read before changing. Inspect existing behavior, tests, migrations, API contracts, Docker, deployment, Nginx, systemd, Celery, env config. Avoid unnecessary rewrites; make incremental changes; add regression tests; run the existing suite; validate the final architecture; document breaking changes. Never assume an existing project already follows this skill.

## 60. Final Principle

Business requirements decide WHAT the system does. This skill decides HOW the DRF backend is structured, configured, implemented, tested, documented, containerized, deployed, and maintained. It stays generic and domain-agnostic.

## 61–82. API Rate Limiting

Goal: protect against abuse, brute force, floods, DoS patterns, auth attacks, resource exhaustion. Enforced in the backend, not the frontend.

- **Global throttling** (all public APIs must be limited by default):
```python
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("RATELIMIT_ANON", default="60/minute"),
        "user": env("RATELIMIT_USER", default="300/minute"),
        "auth": env("RATELIMIT_AUTH", default="10/minute"),
        "sensitive": env("RATELIMIT_SENSITIVE", default="30/minute"),
        "health": env("RATELIMIT_HEALTH", default="120/minute"),
    },
}
```
- Rates come from env; never hardcode values expected to vary per environment.
- Anonymous: keyed by client IP. Authenticated: keyed by user (not just IP) via `UserRateThrottle`.
- Custom throttles in `common/throttling.py`:
```python
class AuthRateThrottle(UserRateThrottle):
    scope = "auth"

class SensitiveRateThrottle(UserRateThrottle):
    scope = "sensitive"
```
- Auth endpoints (`/api/auth/token/`, `/api/auth/token/refresh/`) use the stricter `auth` scope explicitly.
- Sensitive operations (password reset, OTP, email verification, SMS, payments, account recovery, expensive search, file processing, external API proxies) use the `sensitive` scope.
- Health endpoint gets its own `health` scope (or an internal-only endpoint) so deploy checks aren't blocked; don't fully disable throttling on a public health endpoint without a documented reason.
- Shared cache: single-process local dev may use the default cache. Staging/production with multiple instances MUST use Redis (`RATELIMIT_CACHE_URL`), e.g. DB 0 Celery broker, DB 1 Celery results, DB 2 throttling/cache:
```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("RATELIMIT_CACHE_URL", default="redis://localhost:6379/2"),
    },
}
```
  Never use local in-memory cache for production throttling with multiple instances.
- Exceeding a limit returns HTTP 429 in the standard error structure: `{"success": false, "message": "Request rate limit exceeded.", "errors": {}}`; may include retry headers; don't expose internals.
- Behind Nginx/load balancers/proxies, configure a trusted proxy setup explicitly; never blindly trust client-supplied `X-Forwarded-For`.
- OpenAPI documents 429 for public rate-limited endpoints.
- Rate limiting is independent of Celery (Redis may be shared, but use separate DBs/namespaces).
- Docker staging/production compose files must provide Redis or point to an external Redis when used for throttling.
- Tests (isolated test cache, never production Redis): `test_api_allows_requests_within_rate_limit`, `test_api_rejects_requests_after_rate_limit`, `test_anonymous_user_uses_anonymous_throttle`, `test_authenticated_user_uses_user_throttle`, `test_auth_endpoint_uses_stricter_throttle`, `test_sensitive_endpoint_has_stricter_rate_limit`.
- New APIs inherit global throttling; don't disable it without a documented reason; public APIs must never be unintentionally unlimited.

### Rate-limiting Definition of Done
Global throttling on; anon and authenticated throttled; auth and sensitive endpoints stricter; limits configurable via `.env`; shared cache in horizontally scaled prod; 429 uses standard error structure; tests cover it; OpenAPI documents 429; no endpoint unintentionally bypasses throttling.
