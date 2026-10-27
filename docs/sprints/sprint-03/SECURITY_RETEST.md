# Security Retest (live server), 2026-10-27

Target: https://delivery.hossam-ameen.online and https://api.delivery.hossam-ameen.online (35.226.179.10, nginx + gunicorn + Postgres + Redis, no Docker). Probes were run from outside the server.

| ID | Result | Evidence |
|----|--------|----------|
| VULN-012 (refresh token storage) | FIXED | HttpOnly cookie (QA TASK-045/054); frontend now also sends CSP, `frame-ancestors 'none'`, HSTS, nosniff. |
| VULN-013 (throttle bypass by topology) | FIXED, E2 gate cleared | Ports 8010, 5432, 6379, 8000 closed from outside. 14 logins with rotating forged `X-Forwarded-For` gave 8x 401 then 429. nginx overwrites `X-Forwarded-For` (`$remote_addr`), `NUM_PROXIES=1`. |
| VULN-014 (500 on odd input) | FIXED | 100,000 `[` -> 400. 3 MB body -> 413. 100 KB body to `/auth/*` -> 413 at nginx (`client_max_body_size 64k`). |
| VULN-015, 016, 017, 018 | FIXED | Already in code with tests (login max_length, exact-username match, refresh-family revoke on reuse/password change/deactivation, case-insensitive unique email). |
| VULN-019 (no-store) | FIXED | `Cache-Control: no-store` on `/auth/token/` (live). |
| VULN-021 (seed_demo) | FIXED | `seed_demo` now refuses production/staging settings even with `--force` (test added). |
| BUG-010 | FIXED | Non-secret `delivery.has_session` marker; "session expired" shown only if it was set (2 Vitest tests). |
| Server banner | FIXED | `server_tokens off` globally (also on the 301 redirect). |
| Frontend headers | FIXED | HSTS, nosniff, X-Frame-Options DENY, Referrer-Policy, COOP, Permissions-Policy, CSP. |

Not changed (accepted): `/admin/login/` is publicly reachable (protected by Django auth plus the admin login throttle); VULN-020 and VULN-022 (Info).
Open, not security: none.
