# TASK-045: Refresh cookie, Origin check, and reuse detection

- **Backlog item:** BL-012, BL-013; VULN-012, VULN-017 (reuse half)
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-044
- **Estimate:** M

## Description
Stop returning the refresh token in JSON. Put it in the `delivery_refresh` cookie described in the Sprint 03 contract, and treat reuse of an old refresh token as a stolen session.

## Technical Notes
- Implement only what TASK-044's contract says for `POST /auth/token/`, `POST /auth/token/refresh/`, and `POST /auth/logout/`.
- Set and clear the cookie in the auth views. Business rules stay in `apps/users/services.py` (`rotate_refresh_token`, `logout`).
- `CORS_ALLOW_CREDENTIALS = True`. Do not set `CORS_ALLOW_ALL_ORIGINS`. Development origins stay the explicit localhost list.
- `REFRESH_COOKIE_SECURE` from the environment. Default false in development settings, true in production settings.
- Origin check on refresh and logout only: `Origin` must be in `CORS_ALLOWED_ORIGINS`. Failure is 403 `code: origin_rejected` and must not rotate or blacklist.
- Reuse: presenting a blacklisted refresh token blacklists every outstanding refresh token of that user, clears the cookie, and returns 401. A normal rotation of the current token still returns exactly one success. Keep the row lock from TASK-041. `OperationalError` stays 401.
- Update Sprint 02 auth tests that read `data.refresh` from the body. Do not delete the rotation, throttle, or logout tests. The Django test client must send `Origin` and carry the cookie.
- `Cache-Control` itself is TASK-053. Do not expand into password or user-management endpoints.

## Acceptance Criteria
- [x] Login, refresh, and logout match the contract, including cookie flags
- [x] JavaScript-readable JSON no longer contains a refresh token
- [x] A missing or foreign Origin does not rotate a token
- [x] Reuse of a blacklisted refresh token revokes that user's outstanding refresh tokens
- [x] Parallel refresh still never returns two 200s and never returns 500 (SQLite limit from TASK-041 stays documented)
- [x] Tests written and passing; ruff clean

## Activity Log
- 2026-10-26 — team_leader: Task created from the PO cookie decision.
- 2026-10-26 — backend: Login, refresh, and logout use the `delivery_refresh` cookie (`HttpOnly`, `SameSite=Strict`, `Path=/api/v1/auth/`). JSON no longer contains a refresh token. Refresh and logout require `Origin` in `CORS_ALLOWED_ORIGINS` (403 `origin_rejected`, cookie unchanged). Reuse of a blacklisted refresh token blacklists that user's outstanding refresh tokens. `CORS_ALLOW_CREDENTIALS` is true. `REFRESH_COOKIE_SECURE` defaults false in development and true in production. Logout of a missing, expired, or junk cookie is 200 and clears the cookie. Full suite 298 passed; ruff clean. SQLite parallel test still allows zero winners. Status IN_REVIEW. QA and Security retest of the cookie path are not done yet.
- 2026-10-27 — qa: PASS. Backend 298 passed, ruff clean; live black-box 41/41; Vitest and eslint clean; live Chrome run 24/25. Status DONE for QA. VULN-012 is not closed until the Security retest of the cookie path. See QA_REPORT.md.
