# API Contract — Sprint 01

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-001 | **Task:** TASK-001
- **Status:** DRAFT for implementation (contract first; any change goes through Team Leader and must be recorded in the Change Log below)

## Decisions (resolved conflict)

`agents/backend.md` (versioned `/api/v1/`, `{detail, errors}`) and the `drf-backend` skill (`/api/...`, `{success, message, errors}` envelope) disagree. PO decision for Sprint 01:

1. All endpoints live under the **`/api/v1/`** prefix (including health and auth). Docs/schema endpoints live under `/api/` (unversioned).
2. Responses use the **skill envelope**: `{success, message, data}` and `{success:false, message, errors}`. The `{detail}` format is NOT used.
3. Default UI/message language is **English**. Arabic is selected via `Accept-Language: ar`.
4. Celery/Redis are **off** in development settings (`CELERY_ENABLED=False`) and **on in staging only**. No Sprint 01 endpoint depends on them.

Frontend and QA build against this document only.

## Global Conventions

### Base URL and headers
- Dev base URL: `http://localhost:8000` (configurable). All JSON; `Content-Type: application/json`.
- `Accept-Language: ar | en` (also `ar-EG`, `en-US`; quality values honored). Unsupported/missing -> `en`. Affects the `message` field and built-in validation messages in `errors`. Responses include `Content-Language: ar|en`. Field names and machine values (`status`, etc.) are never translated.
- Protected endpoints: `Authorization: Bearer <access>`.

### Success envelope
```json
{ "success": true, "message": "Operation completed successfully.", "data": {} }
```
`data` is an object (or a paginated object for lists). Never null on success; use `{}`.

### Error envelope
```json
{ "success": false, "message": "Validation failed.", "errors": { "field": ["This field is required."] } }
```
- `errors` is always an object. Field errors are `{field: [messages]}`; non-field errors use key `non_field_errors`. For 401/403/404/429/500 `errors` is `{}`.
- No stack traces, paths or internals are ever returned.

| Status | When | `message` (en) | `errors` |
|--------|------|----------------|----------|
| 400 | Validation failure | `Validation failed.` | field map |
| 401 | Missing/invalid/expired token or bad credentials | `Authentication credentials were not provided or are invalid.` | `{}` |
| 403 | Authenticated but not allowed | `You do not have permission to perform this action.` | `{}` |
| 404 | Resource/route not found | `Resource not found.` | `{}` |
| 405 | Method not allowed | `Method not allowed.` | `{}` |
| 429 | Throttled | `Request rate limit exceeded.` | `{}` |
| 500 | Unexpected error | `An unexpected error occurred.` | `{}` |

Examples:
```json
// 401
{ "success": false, "message": "Authentication credentials were not provided or are invalid.", "errors": {} }
// 429  (headers: Retry-After: <seconds>)
{ "success": false, "message": "Request rate limit exceeded.", "errors": {} }
```
Arabic example (`Accept-Language: ar`): `{ "success": false, "message": "تم تجاوز حد الطلبات المسموح به.", "errors": {} }`. Exact Arabic strings are owned by TASK-009 (backend i18n) and are not part of the contract; clients must display `message` as given and key logic on HTTP status, never on message text.

### Pagination (for future list endpoints; none in Sprint 01)
Query: `?page=1&page_size=20` (default 20, max 100). Response:
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": { "count": 0, "next": null, "previous": null, "results": [] }
}
```
`next`/`previous` are absolute URLs or `null`.

### Throttling
All endpoints are throttled by default; rates come from env (defaults shown).

| Scope | Applies to | Key | Default |
|-------|-----------|-----|---------|
| `anon` | unauthenticated requests | client IP | 60/minute |
| `user` | authenticated requests | user id | 300/minute |
| `auth` | `/api/v1/auth/token/`, `/api/v1/auth/token/refresh/` | IP / user | 10/minute |
| `sensitive` | reserved (OTP, password reset, payments; future sprints) | user/IP | 30/minute |
| `health` | `/api/v1/health/`, `/api/v1/health/ready/` | client IP | 120/minute |

Exceeded -> HTTP 429 with the 429 body above and a `Retry-After` header. Clients should back off and not auto-retry in a tight loop.

### Common 4xx/5xx/429 for every endpoint below
Every endpoint can also return 429 and 500 as defined above; they are listed explicitly only where relevant.

---

## GET /api/v1/health/
Basic liveness. Confirms Django is running; does NOT depend on DB, Redis or Celery.
- **Auth:** none, but requires the health password
  - Preferred: header `X-Health-Check-Token: <password>`
  - Fallback (dev/convenience): query `?password=<password>` (appears in access logs; avoid in production)
  - Password is the env var `HEALTH_CHECK_PASSWORD`; never echoed in any response or log.
- **Request:** no body.
- **200:**
  ```json
  { "success": true, "message": "Service is healthy.", "data": { "status": "healthy" } }
  ```
- **403** (password missing or wrong; same body for both so the cases are indistinguishable):
  ```json
  { "success": false, "message": "Invalid health check password.", "errors": {} }
  ```
- **429:** standard rate-limit body (`health` scope).
- **Task:** TASK-004 (throttle scope: TASK-003)

## GET /api/v1/health/ready/
Readiness. Same auth as above.
- **Checks:** database connectivity always; Redis and Celery only when `CELERY_ENABLED=True` (not in development).
- **200:**
  ```json
  {
    "success": true,
    "message": "Service is ready.",
    "data": { "status": "ready", "checks": { "database": "ok" } }
  }
  ```
  When Celery is enabled, `checks` also contains `"redis": "ok"` and `"celery": "ok"`. Checks that are disabled are omitted (not reported as failed).
- **403:** same as basic health.
- **503** (any enabled dependency failing; no internal error details):
  ```json
  {
    "success": false,
    "message": "Service is not ready.",
    "errors": { "checks": { "database": "unavailable" } }
  }
  ```
  Only failing checks are listed under `errors.checks`, valued `"unavailable"`.
- **429:** standard rate-limit body (`health` scope).
- **Task:** TASK-004

## POST /api/v1/auth/token/
Obtain a JWT pair.
- **Auth:** none. Throttle scope `auth` (10/minute default).
- **Request:**
  ```json
  { "username_or_phone": "string", "password": "string" }
  ```
  Both required, non-blank. `username_or_phone` is matched against the username or the phone number.
- **200:**
  ```json
  {
    "success": true,
    "message": "Login successful.",
    "data": { "access": "<jwt>", "refresh": "<jwt>" }
  }
  ```
  Token lifetimes are env-driven (defaults: access 30 min, refresh 7 days). Access token is sent as `Authorization: Bearer`.
- **400:** missing/blank field
  ```json
  { "success": false, "message": "Validation failed.", "errors": { "password": ["This field is required."] } }
  ```
- **401:** wrong credentials or inactive/soft-deleted account (same body for all, no account enumeration)
  ```json
  { "success": false, "message": "Invalid credentials.", "errors": {} }
  ```
- **429:** standard rate-limit body (`auth` scope).
- **Task:** TASK-008 (user model: TASK-005)

## POST /api/v1/auth/token/refresh/
Exchange a refresh token for a new access token.
- **Auth:** none (the refresh token is the credential). Throttle scope `auth`.
- **Request:** `{ "refresh": "<jwt>" }`
- **200:**
  ```json
  {
    "success": true,
    "message": "Token refreshed successfully.",
    "data": { "access": "<jwt>" }
  }
  ```
  Sprint 01 does not rotate refresh tokens, so no new `refresh` is returned. (If rotation is enabled later, `data.refresh` will be added; clients should store it when present.)
- **400:** missing `refresh` -> `errors: { "refresh": ["This field is required."] }`
- **401:** invalid, expired or blacklisted refresh token
  ```json
  { "success": false, "message": "Token is invalid or expired.", "errors": {} }
  ```
- **429:** standard rate-limit body (`auth` scope).
- **Task:** TASK-008

## API documentation endpoints (development/staging only, no envelope)
Served by drf-spectacular; return raw OpenAPI/HTML, not the envelope. Disabled (404) in production unless explicitly enabled. Not throttled under `auth`; subject to `anon`/`user`.

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/schema/` | OpenAPI 3 schema (YAML; JSON via `?format=json`) |
| GET | `/api/docs/` | Swagger UI (HTML) |
| GET | `/api/redoc/` | ReDoc (HTML) |

The schema documents request bodies, the envelope responses, auth, and 429 for the endpoints above.
- **Task:** TASK-008

---

## Task Cross-Reference
| Concern | Task |
|---------|------|
| Envelope, exception handler, throttle classes, pagination | TASK-003 |
| Health endpoints | TASK-004 |
| User model (login by username or phone) | TASK-005 |
| JWT endpoints, OpenAPI, admin | TASK-008 |
| Arabic/English server messages (`Accept-Language`) | TASK-009 |
| Frontend API service and health call | TASK-011 |
| Frontend language header and localized errors | TASK-013 |
| QA backend plan | TASK-021 |


## Out of scope for Sprint 01
No business endpoints (users CRUD, registration, orders, etc.). Seed commands (`create_admin`, `seed_demo`) are CLI only and expose no API.

## Change Log
| Date | Change | By |
|------|--------|----|
| 2026-10-08 | Initial contract | backend |
