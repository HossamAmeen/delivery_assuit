# Delivery Backend (Django + DRF)

## Setup
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
make install-dev
cp .env.example .env      # edit SECRET_KEY etc.; .env is git-ignored
```

## Run
```bash
make run                  # migrates, then serves http://localhost:8000
```
Development settings (`config.settings.development`) use SQLite and need no Redis or Celery.
Schema/docs: `/api/schema/`, `/api/docs/`, `/api/redoc/`.

## Test and lint
```bash
make test                 # pytest + rate-limit tests
make coverage
make check                # manage.py check + makemigrations --check
make lint                 # ruff check .
```

## Create the first Admin
There is no public registration for admins. Create the first one from the CLI:
```bash
ADMIN_USERNAME=admin ADMIN_PASSWORD='<strong password>' make create-admin   # non-interactive (Docker/CI)
python manage.py create_admin --username admin [--phone P] [--email E]       # prompts for the password
```
The password is never accepted as an argument and never printed. Running again for an existing
username makes no change; add `--update-password` to reset it. Do not commit real values.

## Demo data
```bash
DEMO_PASSWORD='<demo password>' make seed-demo
```
Creates one active demo user per role (`demo_admin`, `demo_manager`, `demo_driver`, `demo_trader`,
`demo_client`; driver and trader are approved/active) plus one per non-active status:
`demo_driver_pending` (`pending_approval`) and `demo_client_deactivated` (`deactivated`), for demoing
the status messages. All use `DEMO_PASSWORD`; a re-run resets each account to these values. Safe to run repeatedly (`update_or_create` on username, one transaction). Refuses
when `DEBUG=False` unless run as `python manage.py seed_demo --force`. Each app contributes data
through `apps/<app>/seeders.py` (`seed(password) -> int`). **Limitation:** only users exist in
Sprint 01; shops, items, locations and orders will be added by later sprints' seeders.

## Translations (Arabic / English)
The language comes from the `Accept-Language` header (`ar` or `en`; default `en`). Rule: **every new
user-facing message must use `gettext` / `gettext_lazy`** (never a bare string). After adding one,
add its Arabic text to `locale/ar/LC_MESSAGES/django.po` and run `make compilemessages` (uses
`msgfmt` if installed, otherwise `scripts/compile_messages.py`). Commit the compiled `.mo`.
Clients must key logic on HTTP status, never on message text.

## Rate limiting behind a proxy
Throttling keys on the client IP. `NUM_PROXIES` (env, default `0`) says how many trusted reverse
proxies sit in front of Django: `0` ignores `X-Forwarded-For` completely; `1` (typical Nginx) uses
the address that proxy appended. A wrong value either lets attackers dodge limits (too high) or puts
every user in one bucket (too low). Set `NUM_PROXIES=1` on staging/production behind Nginx.

**`NUM_PROXIES` must equal the real number of trusted proxy hops** (VULN-006, VULN-013). If you add a
CDN or load balancer in front of Nginx, raise it and change the Nginx header handling to match.
Rules for staging/production:
- The backend port is never reachable from outside: the staging compose binds it to `127.0.0.1`
  only, and the firewall allows only 80/443 inbound.
- Nginx must set `X-Forwarded-For` from `$remote_addr` (overwrite, do not append to a client value).
  Use the snippet `docker/staging/nginx-proxy-headers.conf`.
- Retest (THR-1/np1) from outside the host at the first staging deploy: a forged
  `X-Forwarded-For` must get 429 after the limit.

## Admin login lockout
`common.middleware.AdminLoginThrottleMiddleware` counts failed `/admin/login/` attempts in the
shared cache: 5 per IP and 30 per username per 15 minutes (env `ADMIN_LOGIN_MAX_ATTEMPTS`,
`ADMIN_LOGIN_MAX_ATTEMPTS_PER_USERNAME`, `ADMIN_LOGIN_WINDOW_SECONDS`). While locked, even the
correct password gets HTTP 429 until the window ends; a successful login clears the counters.
The per-username cap can lock a real admin out for the window (accepted trade-off). Revisit with
SEC-02 (django-axes or a unified policy).

## Production/staging safety checks
- `config/settings/secrets.py` stops production and staging from starting when `SECRET_KEY` is
  shorter than 32 characters or any secret contains a placeholder such as `change-me`.
- API responses are JSON only (no browsable API).
- Staging defaults to plain HTTP (`SECURE_SSL_REDIRECT=False`, `SECURE_HSTS_SECONDS=0`) until TLS
  exists. **Once TLS is in place set `SECURE_SSL_REDIRECT=True` and a non-zero
  `SECURE_HSTS_SECONDS`; never carry the staging defaults to production.**

## Settings
`config/settings/`: `base` (shared), `development` (SQLite, Celery/Redis off), `staging`
(Celery + Redis cache/throttling on, server only), `production` (PostgreSQL via `DATABASE_URL`,
security flags). Select with `DJANGO_SETTINGS_MODULE`. All configuration comes from environment
variables; see `.env.example`.

## Docker (local)
`docker/local/Dockerfile` (python 3.13-slim, non-root `app` user, deps from
`requirements/development.txt`). `scripts/entrypoint.sh` waits for the database
(`scripts/wait_for_db.sh`, reads `DATABASE_URL`, never prints it), runs `migrate`, then starts the
server. The container `HEALTHCHECK` runs `scripts/healthcheck.py` using `HEALTH_CHECK_PASSWORD`
from the environment. No secrets are baked into the image and `.dockerignore` excludes `.env`.
The compose stack that wires it up is TASK-018. **The Docker files have not been built or run yet**
(PO decision: agents write them only); validate with `docker build -f docker/local/Dockerfile .`.

## JWT sessions (refresh rotation, logout)
`token/refresh/` rotates refresh tokens (the old one is blacklisted); `logout/` blacklists the
refresh token. Access tokens live `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` (default 15) and cannot be
revoked before they expire. Blacklist tables grow, so run `python manage.py flushexpiredtokens`
regularly: manually in local development, via Celery beat (daily) on staging.
