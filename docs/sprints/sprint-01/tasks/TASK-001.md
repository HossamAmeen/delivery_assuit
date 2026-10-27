# TASK-001: Sprint 01 API contract (health, auth, error envelope, i18n)

- **Backlog item:** BL-001
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** —
- **Estimate:** S

## Description
Write `docs/sprints/sprint-01/API_CONTRACT.md` BEFORE any implementation so Frontend and QA can start in parallel. It documents every endpoint Sprint 01 exposes plus the global response/error/throttling/language conventions.

## Technical Notes
- Endpoints to document (all under `/api/v1/` per `agents/backend.md`; see decision note below):
  - `GET /api/v1/health/` - auth: none, password via header `X-Health-Check-Token` (preferred) or query `?password=`. 200 `{"success": true, "message": "Service is healthy.", "data": {"status": "healthy"}}`; 403 (or 401) invalid/missing password `{"success": false, "message": "Invalid health check password.", "errors": {}}`; 429.
  - `GET /api/v1/health/ready/` - same auth; checks DB (Redis/Celery only if enabled).
  - `POST /api/v1/auth/token/` (`{username_or_phone, password}` -> `{access, refresh}` inside the success envelope), `POST /api/v1/auth/token/refresh/`; stricter `auth` throttle scope (default 10/minute).
  - `GET /api/schema/`, `/api/docs/`, `/api/redoc/` (dev only, no envelope).
- Global conventions to document: success envelope `{success, message, data}`; error envelope `{success:false, message, errors}`; 400/401/403/404/429/500 shapes; pagination shape for future lists; `Accept-Language: ar|en` selects message language; throttle scopes and 429 body `{"success": false, "message": "Request rate limit exceeded.", "errors": {}}`.
- DECISION NOTE (conflict to resolve in the contract): `agents/backend.md` says versioned `/api/v1/` and error format `{detail, errors}`; the drf-backend skill says `/api/health/`, `/api/auth/token/` and the `{success, message, errors}` envelope. Sprint 01 follows the skill's envelope and uses the `/api/v1/` prefix for all endpoints. Backend must record this decision at the top of the contract; Frontend/QA build against the contract only.
- Use the template from `agents/backend.md` (Auth / Request / 200 / 4xx / Task) and reference the implementing TASK-ID per endpoint.

## Acceptance Criteria
- [ ] Contract file exists with every endpoint above, request/response/error examples and implementing task IDs
- [ ] Envelope, pagination, throttling (429) and Accept-Language rules documented
- [ ] Frontend (TASK-011) and QA (TASK-021) confirm they can work from the contract alone
- [ ] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-08 — backend: Wrote API_CONTRACT.md (health, auth, envelope, pagination, throttling, i18n; /api/v1/ prefix, skill envelope, EN default, Celery off in dev). Status -> IN_REVIEW. Awaiting Frontend (TASK-011) and QA (TASK-021) confirmation; no code/tests applicable to this docs-only task.
- 2026-10-10 — qa: Backend and frontend both worked from the contract with no mismatches (TASK-021/022); status DONE.
