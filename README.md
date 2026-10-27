# Delivery Platform

Django REST backend + Vue 3 frontend (PWA), bilingual (Arabic/English). Sprint 01 foundation.

## Prerequisites
Docker with the Compose plugin (v2). `make` is optional: every `make` shortcut below also has the plain `docker compose` command next to it.

## Run everything (fresh clone)
1. `cp .env.example .env` and edit it: set `POSTGRES_PASSWORD`, `SECRET_KEY` and
   `HEALTH_CHECK_PASSWORD` (use URL-safe characters in `POSTGRES_PASSWORD`; it is placed in a URL).
2. `docker compose up --build` (or `make docker-local`). The first build downloads images and
   packages and can take several minutes. The command keeps running in that terminal (add `-d` to
   run in the background; follow with `docker compose logs -f`). The backend waits for the database,
   applies migrations and starts; the frontend starts after the backend is healthy. Use a second
   terminal for the next steps.
3. Create the first Admin: set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`, restart the
   backend (`docker compose up -d backend`) so it sees them, then `make docker-create-admin`
   (without make: `docker compose exec backend python manage.py create_admin`).
   Optional demo users: set `DEMO_PASSWORD`, then `make docker-seed`
   (without make: `docker compose exec backend python manage.py seed_demo`).
4. Open:
   - Frontend: http://localhost:5173 (the home page should show **Healthy**)
   - API health: http://localhost:8000/api/v1/health/ (send header `X-Health-Check-Token`)
   - API docs: http://localhost:8000/api/docs/
   - Admin site: http://localhost:8000/admin/ (log in with `ADMIN_USERNAME` / `ADMIN_PASSWORD`)

Stop with `make docker-down`. Data lives in the `db_data` volume and survives restarts;
`make docker-reset` deletes it.

## Environment variables (`.env`)
| Variable | Purpose |
|----------|---------|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database name, user and password (container) |
| `SECRET_KEY` | Django secret key |
| `HEALTH_CHECK_PASSWORD` | Health endpoint password; also sent by the frontend dev build (browser-visible, dev only) |
| `BACKEND_PORT`, `FRONTEND_PORT` | Ports published on your machine (8000, 5173) |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Read by `create_admin` |
| `DEMO_PASSWORD` | Read by `seed_demo` |

The browser calls the backend through the host port (`VITE_API_URL=http://localhost:8000/api/v1`),
not through the container name.

## Tests
`make docker-test` runs pytest in the backend container and Vitest in the frontend container.
Without Docker: see `backend/README.md` and `frontend/README.md`.

## Staging (server only)
`docker/staging/docker-compose.yml` adds Redis, a Celery worker and Celery beat (enabled on the
server only; local development keeps them off). It is written but has **not been run**; Redis and
Celery readiness checks must be verified on staging.

## Status of the Docker files
Written in Sprint 01 but not yet built or run (see `docs/TODO.md`). CI and systemd deployment are
planned separately.
