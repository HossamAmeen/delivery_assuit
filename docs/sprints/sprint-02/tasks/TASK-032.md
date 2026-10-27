# TASK-032: Logout, refresh-token rotation and blacklist

- **Backlog item:** BL-013
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-031
- **Estimate:** M

## Description
Make logout real on the server and tighten refresh tokens.

## Technical Notes
- Enable `rest_framework_simplejwt.token_blacklist`; `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`. `POST /auth/token/refresh/` now also returns a new `refresh`.
- `POST /auth/logout/` `{refresh}` (authenticated): blacklists the refresh token; 204/200 envelope; idempotent (logging out twice is fine); invalid token -> 400/401 envelope.
- Refresh must fail for a user who is no longer operational (deactivated or soft-deleted). Reuse of a blacklisted refresh token -> 401.
- After logout, the old refresh token cannot create new access tokens; the access token naturally expires within its short lifetime (keep `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` small, e.g. 15; document).
- Add a management/cron note for `flushexpiredtokens` (Celery beat on staging; manual locally).

## Acceptance Criteria
- [x] Reused or logged-out refresh tokens are rejected
- [x] Deactivated user cannot refresh
- [x] Logout twice does not error
- [x] Tests written and passing; coverage >= 80% on new code
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-15 — backend: Implemented. token_blacklist app enabled (its migrations), ROTATE_REFRESH_TOKENS/BLACKLIST_AFTER_ROTATION on, access lifetime default 30 -> 15 min (settings + .env.example). services.rotate_refresh_token (401 if user inactive/pending/deactivated/soft-deleted or token reused) and services.logout (idempotent; 400 only for non-refresh/forged tokens); LogoutView at /auth/logout/ (AllowAny, auth throttle, per API_CONTRACT: refresh token is the credential). Refresh response now includes `refresh`. 13 tests added in apps/users/tests/test_auth.py; full suite 289 passed, ruff clean, makemigrations --check clean. flushexpiredtokens note in backend/README.md. API_CONTRACT unchanged. Status -> IN_REVIEW.
- 2026-10-16 — security: Reviewed. VULN-011 (non-atomic rotation, parallel redemption), VULN-014, VULN-017, VULN-019 relate to this task; see ../SECURITY_REPORT.md.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results" (backend, TASK-039 APPROVED 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
