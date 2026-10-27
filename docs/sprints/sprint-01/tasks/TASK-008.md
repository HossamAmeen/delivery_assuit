# TASK-008: JWT auth endpoints, OpenAPI docs and Jazzmin admin

- **Backlog item:** BL-001
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-005
- **Estimate:** M

## Description
Wire authentication, API docs and admin UI (skill sections 17, 21, 22).

## Technical Notes
- `POST /api/v1/auth/token/` and `/api/v1/auth/token/refresh/` using simplejwt, lifetimes from env, `AuthRateThrottle` explicit. Accept phone OR username as identifier (custom serializer/backend). Responses follow the envelope; failed login -> 401 envelope.
- drf-spectacular: `/api/schema/`, `/api/docs/`, `/api/redoc/` reachable in development; restricted or disabled in production. Document health and auth endpoints incl. 429.
- Jazzmin before `django.contrib.admin` in INSTALLED_APPS with settings from the skill; admin protected by Django auth + staff.

## Acceptance Criteria
- [x] Valid credentials (username or phone) return access+refresh; invalid -> 401 envelope; refresh works
- [x] 11th auth request in a minute returns 429 envelope (test uses isolated cache)
- [x] /api/docs/ renders in development; schema lists health + auth
- [x] /admin/ loads with Jazzmin for the Admin created in TASK-006
- [x] Tests written and passing; coverage >= 80%

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — backend: Implemented POST /api/v1/auth/token/ and /token/refresh/ per API_CONTRACT (username_or_phone, envelope, AuthRateThrottle, 401 without enumeration), apps/users services/serializers/views/urls, docs endpoints gated by API_DOCS_ENABLED (default on; off in production), Jazzmin was already configured and verified. 14 new tests; full suite 88 passing, coverage 96%, ruff clean. Status IN_REVIEW.
- 2026-10-10 — qa: TASK-021 backend QA PASS (see QA_REPORT.md); status DONE.
