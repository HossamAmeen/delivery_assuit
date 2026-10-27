# TASK-003: Backend common infrastructure (responses, exception handler, base model, throttling)

- **Backlog item:** BL-001
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-002
- **Estimate:** M

## Description
Implement the shared `common/` package so every later feature gets consistent behavior (skill sections 10-13, 19-20, 61-82).

## Technical Notes
- `common/models.py` `BaseModel` (created_at, modified_at, deleted_at) abstract; `common/managers.py` ActiveManager/DeletedManager/AllManager; soft_delete()/restore() helper.
- `common/responses.py`: `success_response(data, message)` helper; optional renderer so success responses follow `{success, message, data}`.
- `common/exception_handler.py` wired as DRF `EXCEPTION_HANDLER`: validation (400, `errors` per field), auth (401), permission (403), not found (404), throttled (429 `Request rate limit exceeded.`), custom app exceptions (`common/exceptions.py`), unexpected (500 generic message, no stack trace/paths).
- `common/pagination.py` default page-number pagination (page size from env), response follows the envelope.
- `common/permissions.py` placeholder base permissions; `common/throttling.py` with `AuthRateThrottle` (scope auth), `SensitiveRateThrottle` (scope sensitive), `HealthRateThrottle` (scope health).
- DRF settings: global `AnonRateThrottle` + `UserRateThrottle`; rates from `RATELIMIT_*` env; test settings use an isolated locmem cache.

## Acceptance Criteria
- [ ] Unit tests: base model/soft delete/managers; each exception type returns the standard error envelope; 500 never leaks internals
- [ ] Throttle tests: `test_api_allows_requests_within_rate_limit`, `test_api_rejects_requests_after_rate_limit`, `test_anonymous_user_uses_anonymous_throttle`, `test_authenticated_user_uses_user_throttle`, `test_auth_endpoint_uses_stricter_throttle`, `test_sensitive_endpoint_has_stricter_rate_limit` (429 uses envelope)
- [ ] Coverage >= 80% on new code; ruff clean
- [ ] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-08 — backend: Implemented common/ (BaseModel, managers, responses + EnvelopeJSONRenderer, exception handler + handler404/500, pagination, permissions, throttles) wired in settings; 35 tests pass, 94% coverage on common/, ruff/check/makemigrations clean. Status IN_REVIEW.
- 2026-10-10 — qa: TASK-021 backend QA PASS (see QA_REPORT.md); status DONE.
