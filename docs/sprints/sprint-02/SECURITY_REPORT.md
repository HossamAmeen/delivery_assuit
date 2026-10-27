# Security Report — Sprint 02

## Summary
- Critical: 0 | High: 0 | Medium: 3 | Low: 6 | Info: 3 (VULN numbering continues from Sprint 01: VULN-011 to VULN-022)
- **Release decision: PASS** for the Sprint 02 code. No Critical or High finding is open.
- **Retest update (2026-10-17):** VULN-011 and VULN-013 are FIXED WITH CONDITIONS, see section "Retest" at the end. Release decision for the Sprint 02 code stays PASS.
- Conditions: the three Medium findings (VULN-011, VULN-012, VULN-013) go to the Team Leader as fix tasks for the next sprint. **VULN-013 must be fixed before any staging or production deployment** (a DevOps gate, not a code blocker for this sprint). Backend code changes were not made by Security.
- Sprint 01 carry-overs: VULN-001/002 re-verified on the new login flow; VULN-009 (no rotation/blacklist/logout) is closed by TASK-032, with the race caveat in VULN-011.

## Scope and method
- Target: local dev backend only (`config.settings.development` with `DEBUG=False`, throw-away SQLite DB, throw-away secrets, seeded with `seed_demo --force`). No Docker, no production or third-party systems. All servers were started by Security and stopped afterwards (`pgrep -af runserver` empty).
- Static review: `apps/users/*` (models, managers, authentication, permissions, phone, serializers, services, views, urls, seeders), `apps/core/.../seed_demo.py`, `common/*`, `config/settings/*`, `config/urls.py`, `docker/staging/docker-compose.yml`, and frontend `stores/auth.js`, `api/http.js`, `api/auth.js`, `router/index.js`, `LoginView.vue`, `utils/authErrors.js`, plus a search for `v-html`, `innerHTML`, `eval`, storage use and redirects in `frontend/src`.
- Dynamic: `security/pentest_sprint02.py` (about 130 checks, output `security/pentest_sprint02.out`). A second small run captured server tracebacks for the 500 responses (race, deep JSON, big body).
- Not covered: real browser XSS execution (static review only; Vue escapes all interpolation), Docker/staging/production runs, TLS and production-mode headers, a real Nginx in front, PostgreSQL-specific behaviour, authorization of later-sprint endpoints (none exist; the role matrix is covered only by QA's unit tests).

## Tools Run
- bandit 1.9.4 (backend source, tests and migrations excluded): 0 issues (output `security/bandit.out` contains only comment warnings).
- pip-audit on `requirements/staging.txt`: no known vulnerabilities (`security/pip-audit.out`).
- `npm audit` (all and `--omit=dev`): 0 vulnerabilities (`security/npm-audit.out`).
- gitleaks: not available; replaced by a regex search for hard-coded secrets (only docs placeholders and the storage-key name `delivery.refresh_token` matched). No `.env` file in the tree; `.gitignore` lists `.env`, `db.sqlite3`. The project is not a git repository, so history could not be scanned.
- Manual review and the scripted pentest above. OWASP ZAP not used.

## Findings

### VULN-011: Refresh-token rotation is not atomic; one refresh token can be redeemed more than once
- **Severity:** Medium
- **Category:** OWASP API2 Broken Authentication (CWE-362 race condition)
- **Location:** `backend/apps/users/services.py:rotate_refresh_token` (validation `RefreshToken(raw)` happens before and outside the transaction that calls `token.blacklist()`)
- **Description:** the blacklist check and the blacklisting are separate steps. Concurrent requests with the same refresh token all pass the check.
- **Evidence:** 10 parallel `POST /auth/token/refresh/` with one refresh token (3 rounds, SQLite): 2 returned 200 with two different valid new token pairs each round; the rest returned 500 (`database is locked`, an SQLite artefact; on PostgreSQL the losers are more likely to succeed too). Sequential reuse is correctly refused (401).
- **Impact:** the "old token stops working" guarantee can be defeated by an attacker holding a stolen refresh token who races the victim, and each success yields a new 7-day token chain. Also unhandled DB errors surface as 500.
- **Remediation:** make rotation single-use at the database level: inside `transaction.atomic()` lock the `OutstandingToken` row (`select_for_update`) and create the `BlacklistedToken` first (unique constraint), treating a conflict as `TokenError` (401). Add a concurrency test on PostgreSQL. Consider revoking the whole token family on detected reuse (see VULN-017).
- **Status:** FIXED WITH CONDITIONS (retest 2026-10-17: verified on SQLite; strict exactly-one-200 is PostgreSQL-only and was not run)

### VULN-012: Refresh token kept in `localStorage` (7 days) with no CSP
- **Severity:** Medium
- **Category:** OWASP A02/A07, CWE-922 Insecure Storage of Sensitive Information
- **Location:** `frontend/src/stores/auth.js` (`REFRESH_STORAGE_KEY`, `writeStored`), `frontend/index.html` (no CSP meta), no static-host headers in the repo
- **Description:** the access token is kept in memory only (good), but the 7-day refresh token is readable by any script on the origin. The app has no `v-html`/`innerHTML`/`eval` (checked), so no XSS sink exists today, but there is no CSP as a second layer and a single future XSS or compromised dependency would hand over a long-lived session that works from any machine. Server-side there is no reuse detection (VULN-017), so the victim is not alerted either.
- **Evidence:** static review; the key `delivery.refresh_token` is written on login and rotation. The Team Leader flagged this decision for Security.
- **Impact:** XSS or a malicious browser extension means persistent account takeover (driver, trader and admin accounts included).
- **Remediation:** preferred: refresh token in an `HttpOnly; Secure; SameSite=Strict` cookie scoped to `/api/v1/auth/` (needs a CSRF token or origin check on refresh/logout). Otherwise: add a strict CSP from Nginx (`default-src 'self'`, no inline scripts, `frame-ancestors 'none'`), shorten refresh lifetime for admin/manager, and keep the no-`v-html` rule enforced by ESLint (`vue/no-v-html`).
- **Status:** OPEN

### VULN-013: Staging compose publishes the backend port directly while `NUM_PROXIES=1`, re-opening the throttle bypass (regression of VULN-001 by topology)
- **Severity:** Medium
- **Category:** OWASP API4 Unrestricted Resource Consumption / A05 (CWE-348)
- **Location:** `docker/staging/docker-compose.yml:51` (`"${BACKEND_PORT:-8000}:8000"`, all interfaces), `backend/docker/staging/Dockerfile:27` (gunicorn `0.0.0.0:8000`), `NUM_PROXIES` default `1`
- **Description:** with `NUM_PROXIES=1` DRF trusts the last `X-Forwarded-For` entry. That is only correct if every request passes through the proxy that appends the real client IP. The compose file also exposes gunicorn directly.
- **Evidence (dev server, the same code path):** `NUM_PROXIES=0`: 25 logins with rotating forged `X-Forwarded-For` gave 10 x 401 then 15 x 429 (safe); 40 registrations gave 30 x 201 then 10 x 429 (safe). `NUM_PROXIES=1` with a forged header sent straight to the app: 25 x 401, 0 x 429 for login; 40 registrations all processed (no limit hit). `X-Real-IP`, `Forwarded`, `True-Client-IP`, `CF-Connecting-IP` do not affect the key in either mode.
- **Impact:** if port 8000 is reachable from outside, the login limit (10/min) and registration limit (30/min) can be bypassed, giving unlimited password guessing and account spam.
- **Remediation:** publish the backend on loopback or the Docker network only (`127.0.0.1:8000:8000` or no `ports:`), allow only Nginx to reach it (firewall), and make Nginx set `X-Forwarded-For` with `$remote_addr` (not append to a client-supplied value) or confirm `proxy_add_x_forwarded_for` is used with exactly one hop. Document it next to VULN-006.
- **Status:** FIXED WITH CONDITIONS (retest 2026-10-17: fix verified by review; outside-the-host retest deferred to the first staging deploy, which stays a DevOps gate)

### VULN-014: Unhandled exceptions return 500 on unauthenticated input (deep JSON, oversized body, odd token claim)
- **Severity:** Low
- **Category:** OWASP A05 / API8 Security Misconfiguration (CWE-248, CWE-400)
- **Location:** DRF JSON parsing and `common/exception_handler.py`; token claims handling in `StatusCheckingJWTAuthentication`
- **Evidence:** `POST /auth/register/client/` with 100,000 `[` characters -> 500 (`RecursionError` in the JSON parser; the same payload with `{` gives 400). Any request body above Django's 2.5 MB `DATA_UPLOAD_MAX_MEMORY_SIZE` -> 500 (`RequestDataTooBig` is not mapped to 400/413). A correctly signed access token whose `user_id` is a non-integer string -> 500 (needs the signing key, so key-compromise only). Responses are the generic envelope; no stack trace leaks (verified), but each 500 logs a traceback and can trigger error alerts.
- **Impact:** noise and cheap log/alert flooding; no data exposure.
- **Remediation:** map `RecursionError` and `SuspiciousOperation`/`RequestDataTooBig` to 400/413 in the exception handler (or a small middleware), limit body size at Nginx (`client_max_body_size 64k` for the auth routes), and cap JSON nesting.
- **Status:** OPEN

### VULN-015: Login accepts unbounded identifier and password length
- **Severity:** Low
- **Category:** OWASP API4 (CWE-400)
- **Location:** `backend/apps/users/serializers.py:LoginSerializer` (no `max_length`; registration caps password at 128 and phone at 32)
- **Evidence:** a 2 MB password or a 2 MB identifier takes about 1.35 s per request (hashing/normalisation) versus about 0.83 s for a normal wrong-password attempt (the PBKDF2 hash dominates both).
- **Impact:** small amplification; bounded by the 10/min/IP throttle and the 2.5 MB body limit.
- **Remediation:** `max_length=150` for `username_or_phone` and 128 for `password` on login (return the generic 401/400).
- **Status:** OPEN

### VULN-016: Login identifier normalisation is too lenient
- **Severity:** Low
- **Category:** OWASP A07 (CWE-20)
- **Location:** `services.authenticate_user` / `phone.normalize_phone` (all non-digit characters are dropped from any identifier)
- **Evidence:** `x01000000005` and `abc-0100-0000-005-zzz` authenticate as the account with phone `01000000005` (200 with the correct password). Also the query ORs `username` and `phone` and takes `.first()`, so an identifier could match two different accounts in theory.
- **Impact:** no bypass of the password; makes identifier handling ambiguous and may confuse audit logs and future lockout keyed by identifier.
- **Remediation:** only normalise when the identifier looks like a phone (digits, spaces, dashes, `+`, brackets, Arabic digits only); otherwise match the username exactly. Prefer the exact username match over the phone match.
- **Status:** OPEN

### VULN-017: No refresh-token reuse detection; sessions survive password changes
- **Severity:** Low
- **Category:** OWASP API2 (CWE-613)
- **Evidence:** after an old (rotated) refresh token was presented and refused, the legitimate new refresh token still worked (200). After a password change in the database, the previously issued access (200) and refresh (200) tokens still worked. Access tokens issued before rotation or logout stay valid up to 15 minutes (documented).
- **Impact:** a thief who replays an old token is not detected and the victim is not logged out; once password recovery arrives (Sprint 03) a reset would not end a hijacked session.
- **Remediation:** on reuse of a blacklisted refresh token blacklist all outstanding tokens of that user; blacklist all of a user's tokens when the password is changed/reset or the account is deactivated; schedule `flushexpiredtokens`.
- **Status:** OPEN (must be done together with Sprint 03 password recovery at the latest)

### VULN-018: Phone numbers and emails are unverified and email uniqueness is only an application check
- **Severity:** Low
- **Category:** OWASP A07 / API6 (CWE-287, CWE-362)
- **Location:** `RegisterSerializer` / `services.email_exists`; `User.email` has no unique constraint
- **Evidence:** any client can register any phone number (the real owner then gets "already exists"); duplicate email check is case-insensitive in code but not enforced by the database, so concurrent registrations can create duplicates. Duplicate phone/email messages disclose registered values (accepted by the contract; mitigated by the 30/min throttle; the existing-phone path answers in about 4 ms versus 830 ms for a new phone, which only repeats what the body already says).
- **Impact:** number squatting and pre-registration of someone else's phone before recovery/OTP exists; weaker account recovery later.
- **Remediation:** phone/email verification (OTP) before password recovery is built; add a unique constraint on a normalised (lower-cased) email where non-empty.
- **Status:** OPEN (track for Sprint 03)

### VULN-019: Token responses are not marked non-cacheable
- **Severity:** Low
- **Category:** OWASP A05 (CWE-525)
- **Evidence:** `POST /auth/token/` 200 has no `Cache-Control`, no `Pragma`; `GET /auth/me/` also has none.
- **Impact:** a shared cache or browser could store tokens or profile data.
- **Remediation:** `Cache-Control: no-store` on all `/api/v1/auth/*` responses (small middleware or per-view decorator).
- **Status:** OPEN

### VULN-020 (Info): Public development `SECRET_KEY` fallback
- `config/settings/development.py` falls back to `insecure-development-only-key`. With it, anyone can mint an access token for any user id (I confirmed that a validly signed token is accepted, so the only barrier is the key). Production/staging refuse placeholder and short keys (`secrets.py`, verified in Sprint 01) and `wsgi.py`/`asgi.py` default to production. Keep dev servers off public networks. The dev server also sends `Server: WSGIServer/0.2 CPython/3.12.3` and serves `/api/schema/` and `/api/docs/` (production default is off).

### VULN-021 (Info): `seed_demo` creates a superuser with a well-known username
- `demo_admin` is `is_superuser`/`is_staff` with a predictable username and phone, all demo users share one password, and password validators are bypassed. The command refuses to run when `DEBUG=False` unless `--force`. Never run it with `--force` on staging/production; consider also refusing when `DJANGO_SETTINGS_MODULE` is staging/production.

### VULN-022 (Info): Auth throttle is per IP only and shared by login, refresh and logout
- One bucket of 10/min per IP covers login, refresh and logout. Many users behind one NAT/CGNAT address can lock each other out of login for a minute, and a distributed attacker is not slowed per account. Consider an additional per-identifier limit with backoff and a higher limit for refresh.

## Checked and fine
- **Enumeration (login):** wrong-password responses for unknown identifier, unknown phone, active, pending, deactivated and admin accounts are byte-identical (status 401, same body and content type). Median timing 821 to 825 ms across all five (ratio 1.01), so VULN-002's fix holds. Pending/deactivated status is only shown after the correct password (403 with `code`).
- **Mass assignment:** `role`, `status`, `is_staff`, `is_superuser`, `is_active`, `username`, `id`, `groups`, `user_permissions`, `deleted_at`, `last_login` in the body (JSON and form-encoded) are ignored; DB rows were driver/trader `pending_approval` and client `active`, not staff, no username. No admin/manager register route (404). `PUT/PATCH/DELETE/POST /auth/me/` give 405.
- **Privilege/status:** a client bearer token is not accepted by the Django admin; a non-staff account with the right password is refused by `/admin/login/`. Status is re-checked on every request: deactivated -> 403 (`/me`) and 401 on refresh; pending -> 403; `is_active=False` -> 401 on access and refresh; soft-deleted -> 401 on access, login and refresh. Role is read from the database on each request, so a role change applies immediately (token carries only `user_id`, `jti`, `exp`, `iat`, `token_type`).
- **JWT:** `alg=none`, wrong key, swapped payload with the original signature, expired token, refresh used as access, access used as refresh and as logout input, missing `token_type`, forged `token_type=refresh`, nonexistent and null `user_id`, HS384/HS512, lowercase `bearer`, `Token` scheme, trailing junk and `?access_token=` were all refused (401, or 400 for logout). Reuse after rotation and after logout is refused. Access lifetime 15 min and refresh 7 days as documented.
- **Throttle (NUM_PROXIES=0, the default):** forged `X-Forwarded-For`, `X-Real-IP`, `Forwarded`, `X-Client-IP`, `True-Client-IP`, `CF-Connecting-IP` do not create new buckets for login (11th request -> 429) or registration; the `//` path variant is a 404.
- **Injection and errors:** SQL/template/NUL/long strings in the login identifier give 400/401; malformed, wrong-type and empty JSON bodies give 400; wrong methods 405, TRACE 405, unknown route 404 with the JSON envelope; no tracebacks or framework internals in any response with `DEBUG=False`. Bad `Host` header -> 400.
- **CORS:** only `http://localhost:5173` receives `Access-Control-Allow-Origin`; `evil.example.com`, `null`, `localhost:5173.evil.com` and `evil.localhost:5173` get none; no `Allow-Credentials`.
- **Headers (dev):** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, COOP `same-origin`; no cookies set by the API. HSTS/secure cookies/SSL redirect exist only in production settings (read, not run).
- **XSS/storage (static):** no `v-html`, `innerHTML`, `eval` or `document.cookie` in `frontend/src`; names and server messages are rendered through `{{ }}` (escaped); API responses are `application/json` with `nosniff`, so stored `<script>` in `full_name` is inert. Access token is memory-only; only the refresh token is persisted (VULN-012). No open redirect (the router never reads a `redirect`/`next` query). Guards use store state, not token text; they are UX only and the server enforces access. The health token marker was absent from the production bundle in Sprint 01 and `.env.example` still holds only an empty `VITE_HEALTH_CHECK_TOKEN`.
- **Secrets in repo:** none found; `.env` ignored; demo password is read from `DEMO_PASSWORD` and not printed.

## Workflow notes
- No product code was modified by Security. Fix tasks for VULN-011 to VULN-019 are for the Team Leader. Suggested grouping: backend (VULN-011, 014, 015, 016, 017, 019), frontend/DevOps (VULN-012, CSP via Nginx), DevOps (VULN-013).
- Retest plan after fixes: re-run `security/pentest_sprint02.py` (JWT-14 should show exactly one 200; ERR-1/DOS-3 no 500; THR-1/np1 in a topology where the backend is not reachable directly).
- Artifacts: `security/pentest_sprint02.py`, `security/pentest_sprint02.out`, `security/bandit.out`, `security/pip-audit.out`, `security/npm-audit.out`. The script uses throw-away secrets only.
- One script line (PRIV-1) printed FINDING because `urllib` followed the redirect to the admin login page (HTTP 200 of the login form); it was verified as a false positive, the bearer token is not accepted by the admin site.


## Retest (2026-10-17): TASK-041 (VULN-011) and TASK-043 (VULN-013)
Scope: only these two fixes. Security changed no product code and wrote no APPROVAL.md. Docker and docker compose were NOT run (project rule). Script: `security/retest_sprint02.py`, output: `security/retest_sprint02.out` (venv, fresh SQLite, `config.settings.development`, `DEBUG=False`, threaded `runserver`; all servers stopped, `pgrep` shows none).

### VULN-011 / TASK-041: FIXED WITH CONDITIONS
- Code review (`apps/users/services.py:rotate_refresh_token`): inside `transaction.atomic()` the `OutstandingToken` row is locked (`select_for_update`), then `token.blacklist()` claims the token; `created=False` raises `TokenError` (401). The new pair is created only after the claim, in the same transaction. `OperationalError` (lock, busy, deadlock) becomes `TokenError` (401 with the generic envelope) and the transaction rolls back, so no pair is issued and the token is not burned. The earlier validation `RefreshToken(raw)` still runs outside the transaction, but it is now only a fast pre-check; the unique BlacklistedToken row is the real gate. No new issue found; no information leak (same generic message for every failure). `logout()` is unchanged and idempotent.
- Dynamic (JWT-14): 6 races (10 and 30 parallel threads, 3 rounds each): every race gave exactly 200 x1 and 401 for the rest; **0 x 500**, no second pair. Old token refused afterwards (401) in 6/6. Winner's access token works on `/auth/me/` and the winner's refresh rotates again (200) in 6/6; the winner's rotated-away refresh is refused. (Before the fix: 2 of 10 succeeded and the rest were 500.)
- Reuse: rotate 200 then reuse 401; refresh after logout 401; logout of a rotated-away token idempotent; reuse error uses the standard envelope.
- Lock-error path: with an external exclusive SQLite write lock held, refresh returned **401 after the 5 s busy timeout (no 500)**; after releasing the lock the same token still rotated once (200) and then was single-use (401). Side note (Info): the loser waits up to the DB busy timeout, and a legitimate client on a busy DB gets 401 instead of 503 (QA N-21), so it must log in again.
- **Conditions:** the strict "exactly one 200" guarantee relies on row locking and unique-constraint semantics that were verified only on SQLite (which serialises writers, so the observed "exactly one" is not proof for PostgreSQL). The PostgreSQL run was NOT done (no Docker/PostgreSQL locally). Run the threaded test and JWT-14 against PostgreSQL in CI or at the first staging deploy. Reuse detection / family revocation remains VULN-017 (Low, out of scope).

### VULN-013 / TASK-043: FIXED WITH CONDITIONS (review only)
- Read: `docker/staging/docker-compose.yml` publishes the backend as `127.0.0.1:${BACKEND_PORT:-8000}:8000` (loopback only; the only `ports:` entry for the app); `docker/staging/nginx-proxy-headers.conf` sets `X-Forwarded-For $remote_addr` (overwrite, not `$proxy_add_x_forwarded_for`), plus X-Real-IP, X-Forwarded-Proto, Host, and states one hop = `NUM_PROXIES=1`; `backend/README.md` ("Rate limiting behind a proxy") and `backend/.env.example` document that NUM_PROXIES must equal the real hop count, the loopback bind, firewall 80/443 only, and the outside retest. Code default stays safe (`NUM_PROXIES=0`; compose default 1 only behind Nginx).
- Local behaviour check of THR-1 (direct to the dev app, not a staging topology): `NUM_PROXIES=0`: 10 x 401 then 15 x 429 (forged header ignored, limit holds). `NUM_PROXIES=1`: 25 x 401, 0 x 429 (forged header honoured). This matches the documentation: with NUM_PROXIES=1 the limit holds only if the app is unreachable except through Nginx, which the loopback bind and the overwrite snippet provide.
- **Conditions (deferred to the first staging deploy, a DevOps gate):** (1) THR-1/np1 from outside the host: a forged `X-Forwarded-For` must reach 429 after the limit; (2) confirm port 8000 is bound to 127.0.0.1 only (`ss -ltnp`) and the firewall allows only 80/443; (3) confirm the real Nginx config includes the snippet (the repo has no full site template) and the staging env has `NUM_PROXIES=1`; (4) a containerised Nginx must use `backend:8000` on the compose network. Gunicorn still binds 0.0.0.0 inside the container, which is acceptable only because of the loopback publish. Nothing about the deployed topology was executed.

### Final release decision, Sprint 02 code
- Critical 0 | High 0 | Medium open: VULN-012 (deferred to Sprint 03 by PO decision), VULN-011 and VULN-013 fixed with conditions | Low 6 | Info 3.
- **Release decision: PASS** for the Sprint 02 code (no Critical/High open). Conditions carried forward: PostgreSQL run of the strict single-200 test (VULN-011), and the VULN-013 outside-the-host retest plus the items above before any staging/production deploy. Security's sign-off is NOT an APPROVAL.md; that needs Backend and QA.
