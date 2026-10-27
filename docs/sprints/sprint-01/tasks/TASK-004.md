# TASK-004: Health check API (basic and readiness) with tests

- **Backlog item:** BL-001
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-003
- **Estimate:** S

## Description
Implement the health endpoints from the skill (sections 23-27). This is the endpoint the frontend calls end to end.

## Technical Notes
- Create a small `apps/core` (or `common` view module) app with `GET /api/v1/health/` and `GET /api/v1/health/ready/`.
- Password from `settings.HEALTH_CHECK_PASSWORD` (env). Accept `X-Health-Check-Token` header (preferred) or `?password=`. Compare with `secrets.compare_digest`. Never log or return the password, env vars, DB credentials, paths or stack traces.
- Basic health only proves Django is up; must not depend on DB/Redis/Celery. Ready checks the DB; checks Redis/Celery only when enabled.
- Explicit `permission_classes = [AllowAny]` (access controlled by the password), `throttle_classes = [HealthRateThrottle]` (scope `health`, default 120/minute). Documented in OpenAPI incl. 429.
- CORS must allow the frontend origin (env) and the `X-Health-Check-Token` header.

## Acceptance Criteria
- [x] `test_health_endpoint_returns_success_with_valid_password`, `test_health_endpoint_rejects_invalid_password`, `test_health_endpoint_requires_password`, `test_health_endpoint_does_not_expose_secret` pass
- [x] Readiness tests cover DB failure (mocked) -> failure envelope; works with `CELERY_ENABLED=False`
- [x] Response bodies match API_CONTRACT.md exactly
- [x] Tests written and passing; coverage >= 80%

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-08 — backend: Implemented apps/core health API (GET /api/v1/health/ and /ready/), CORS allow-header x-health-check-token, 11 tests (apps/core/tests/test_health.py); core coverage 93%. check, makemigrations --check, ruff, make test (47 passed) all green. Status -> IN_REVIEW.
- 2026-10-10 — qa: TASK-021 backend QA PASS (see QA_REPORT.md); status DONE.
