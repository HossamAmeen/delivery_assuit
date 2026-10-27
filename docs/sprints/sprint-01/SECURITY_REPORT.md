# Security Report — Sprint 01

## Summary
- Initial review: Critical 0 | High 1 | Medium 3 | Low 3 | Info 4 (release BLOCKED)
- After fixes and retest (2026-10-10): **Critical 0 | High 0 | Medium 0 open | Low 0 open**; Info items remain as notes
- **Release decision: PASS** for Sprint 01 code, with the conditions listed under "Retest" (no Docker/staging/production environment was tested)

## Scope and method
- Target: local development server only (`config.settings.development`, throw-away SQLite DB, own admin account). No production or third-party systems.
- Code reviewed: `backend/config/settings/*`, `common/*`, `apps/core`, `apps/users`, `scripts/*`, Dockerfiles, compose files, `frontend/src/*`, built bundle.
- Not tested (not built yet): authorization/IDOR, file uploads, role permissions, JWT-protected endpoints (none exist in Sprint 01), the running Docker/staging stacks.

## Tools Run
- bandit 1.9 on backend source (excluding tests/migrations): 1 Medium, a false positive (VULN-010).
- pip-audit on `requirements/staging.txt`: no known vulnerabilities.
- `npm audit` (all and production-only): 0 vulnerabilities.
- gitleaks: **not available**; replaced by a pattern search for hard-coded secrets (clean) and a bundle check (below). The project is not a git repository, so history could not be scanned.
- Manual dynamic tests (script kept outside the repo): security headers, CORS, content negotiation, injection strings, JWT tampering, user-enumeration timing, rate-limit bypass, admin login brute force.
- Production bundle built with `VITE_HEALTH_CHECK_TOKEN=SECRETMARK…`: the marker is **not** in `dist/` (token correctly dev-only). No `v-html`, `innerHTML` or `eval` in `frontend/src`; only `localStorage` use is the language setting.

## Findings

### VULN-001: Login and health rate limits can be bypassed with a forged `X-Forwarded-For`
- **Severity:** High
- **Category:** OWASP API4 Unrestricted Resource Consumption / API2 Broken Authentication (CWE-307)
- **Location:** `backend/config/settings/base.py` (`REST_FRAMEWORK`, no `NUM_PROXIES`), `common/throttling.py`
- **Description:** DRF builds the throttle key from `X-Forwarded-For` when present. With `NUM_PROXIES` unset it trusts the whole client-supplied header, so each new header value is a new bucket.
- **Evidence:** 30 login attempts with different `X-Forwarded-For` values: all 30 processed (401). 15 attempts without the header: 1 processed, 14 blocked (429).
- **Impact:** an attacker can try unlimited passwords against `/api/v1/auth/token/` (the 10/min limit, a Sprint 01 acceptance criterion, gives no protection). Same bypass for the health endpoint limit.
- **Remediation:** set `NUM_PROXIES` to the number of trusted proxies (0 in dev, 1 behind Nginx), make it env-configurable, and add a test that a spoofed header does not create a new bucket. Consider additionally limiting per username.
- **Status:** VERIFIED (fixed in TASK-024; retest 2026-10-10, see Retest)

### VULN-002: Username/phone enumeration through response time
- **Severity:** Medium
- **Category:** OWASP API2 Broken Authentication (CWE-204)
- **Location:** `backend/apps/users/services.py:authenticate_user`
- **Description:** unknown identifiers return immediately; existing accounts run the password hash first.
- **Evidence:** median of 8 wrong-password logins: existing user ≈ 833 ms, unknown user ≈ 5 ms.
- **Impact:** an attacker can list valid usernames and phone numbers, undermining the contract's "no account enumeration" promise (bodies are identical, timing is not).
- **Remediation:** when no user is found, run a dummy `check_password` against a fixed hash so both paths take the same time.
- **Status:** VERIFIED (fixed in TASK-025; retest 2026-10-10, see Retest)

### VULN-003: Django admin login has no brute-force protection
- **Severity:** Medium
- **Category:** OWASP A07 Identification and Authentication Failures
- **Location:** `/admin/login/` (`config/urls.py`)
- **Evidence:** 40 consecutive bad passwords for a real admin account: all 40 processed, no lockout or throttling.
- **Impact:** unlimited guessing against the highest-privilege accounts.
- **Remediation:** throttle or lock out admin login (for example django-axes or a rate-limit middleware for `/admin/login/`), and/or move the admin URL and restrict it by network at Nginx.
- **Status:** VERIFIED (fixed in TASK-025; retest 2026-10-10, see Retest)

### VULN-004: Browsable/HTML API renderer is enabled
- **Severity:** Low
- **Category:** OWASP A05 Security Misconfiguration
- **Location:** `base.py` `REST_FRAMEWORK` (no `DEFAULT_RENDERER_CLASSES`)
- **Evidence:** `Accept: text/html` on the health endpoint returns an HTML page. It also applies to production.
- **Impact:** needless attack surface (forms, CSRF/session interplay); API responses should be JSON only.
- **Remediation:** set `DEFAULT_RENDERER_CLASSES` to JSON only (browsable API in development only if wanted).
- **Status:** VERIFIED (fixed in TASK-026; retest 2026-10-10, see Retest)

### VULN-005: Placeholder secrets accepted outside development (QA BUG-001)
- **Severity:** Low
- **Category:** OWASP A02 Cryptographic Failures / A05
- **Location:** `config/settings/production.py`, `staging.py`; `.env.example`
- **Description:** `SECRET_KEY=change-me` and `HEALTH_CHECK_PASSWORD=change-me` are accepted; a 9-byte key also makes PyJWT warn about key length.
- **Remediation:** in production/staging reject placeholder values and keys shorter than 32 characters at startup.
- **Status:** VERIFIED (fixed in TASK-026; retest 2026-10-10, see Retest)

### VULN-006: Staging compose defaults weaken transport security
- **Severity:** Low
- **Category:** OWASP A05
- **Location:** `docker/staging/docker-compose.yml` (`SECURE_SSL_REDIRECT` default `False`), `staging.py` (`SECURE_HSTS_SECONDS` default 0)
- **Impact:** a staging server started with defaults serves plain HTTP with no HSTS; acceptable until TLS exists but easy to forget.
- **Remediation:** document in the staging README that both must be enabled once TLS is in place; do not carry the defaults to production.
- **Status:** MITIGATED (README warning added in TASK-026; defaults remain until TLS exists; DevOps must enable TLS redirect and HSTS; not a release blocker)

### VULN-007 (Info): Health endpoint accepts the password in the query string
- Appears in access logs (documented in the contract). Prefer the header only in production; consider removing the fallback.

### VULN-008 (Info): Health password is browser-visible in the dev frontend
- Verified it is absent from the production bundle. In development anyone with the page can read it; keep the health password separate from every other secret.

### VULN-009 (Info): No refresh rotation, blacklist or logout
- Planned for SEC-02. Until then a stolen refresh token is valid for 7 days. Tampered, `alg=none` and access-as-refresh tokens were all rejected with 401.

### VULN-010 (Info): bandit B310 on `scripts/healthcheck.py`
- False positive: the URL is a fixed `http://127.0.0.1:<port>` string. `# nosec B310` with a comment added in TASK-026. Closed.

## Checked and fine
- DRF default permission is `IsAuthenticated`; every public view declares `permission_classes` explicitly.
- Health password compared in constant time and never echoed.
- Injection strings in the login field (`' OR '1'='1`, 5,000 chars, NUL byte) produce 401/400, never 500 or a stack trace.
- CORS: an unknown origin gets no `Access-Control-Allow-Origin`; the configured frontend origin does.
- Headers present in dev: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `COOP`. Production adds HSTS, secure cookies, SSL redirect (read in settings; not run).
- Production settings force `DEBUG=False`; empty `ALLOWED_HOSTS` rejects all hosts; API docs are off in production by default; errors never return internals (unit-tested and observed).
- Containers run as a non-root user; no secrets in Dockerfiles; `.dockerignore` excludes `.env`.

## Workflow notes
- Product code was not modified by Security; fixes were made by Backend in TASK-024/025/026. Fix tasks are for the Team Leader.
- Retest after fixes: VULN-001 (send 30 attempts with rotating `X-Forwarded-For`, expect 429 after 10), VULN-002 (timing within noise), VULN-003 (admin lockout/throttle).

## Retest (2026-10-10, fresh dev server, throw-away database)
| Finding | Test | Result |
|---|---|---|
| VULN-001 | 30 logins rotating `X-Forwarded-For`, `X-Real-IP`, `Forwarded`, `X-Client-IP` | 10 × 401, then 20 × 429 (first 429 at the 11th) VERIFIED |
| VULN-001 | 130 health calls with rotating `X-Forwarded-For` | 120 × 200, then 429 VERIFIED |
| VULN-002 | Median of 3 wrong-password logins | existing 879 ms, unknown 896 ms, inactive 872 ms (was 833 vs 5) VERIFIED |
| VULN-003 | Case, whitespace, zero-width, header and path variants | 5 failures processed, 6th+ 429 for every variant; correct password refused while locked; other username from the same IP also blocked VERIFIED |
| VULN-003 | Path tricks (`//admin/login/`, `/admin/login`, `%2e`, `;x`, double slash) | `//admin/login/` also locked (429); the others only redirect to the login page and never authenticate, so no bypass |
| VULN-004 | `Accept: text/html`, `?format=api`, docs | 406 JSON, 404 JSON, docs 200 VERIFIED |
| VULN-005 | Production settings with `change-me`, short and empty `SECRET_KEY` | refuse to start; a real key starts VERIFIED |
| Regression | Backend suite | 159 passing, coverage 96%, ruff clean, `manage.py check` clean |

### Conditions and limits of this PASS
1. `NUM_PROXIES` must be `1` behind Nginx (staging compose sets it). Verified with unit tests that simulate a proxy-appended header; **not** verified behind a real Nginx.
2. Admin lockout trade-off: a deliberate attacker can lock one admin username (or an office IP) out for 15 minutes. Accepted; revisit in SEC-02.
3. Not covered: Docker/staging/production deployments, TLS and headers in production mode, authorization (IDOR/roles) because those endpoints do not exist yet, and every later sprint.
4. Open notes: VULN-006 (TLS defaults, DevOps), VULN-007..009 (Info).
