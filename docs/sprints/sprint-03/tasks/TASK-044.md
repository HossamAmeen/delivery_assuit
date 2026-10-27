# TASK-044: Sprint 03 API contract

- **Backlog item:** BL-014, BL-015, BL-016, BL-052, BL-059, BL-064, BL-078; VULN-012, VULN-014..019
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** Sprint 02 contract (`docs/sprints/sprint-02/API_CONTRACT.md`)
- **Estimate:** S

## Description
Write `docs/sprints/sprint-03/API_CONTRACT.md` before any Sprint 03 code. Same envelope, `/api/v1/` prefix, `Accept-Language`, and throttling rules as Sprint 01 and Sprint 02. Record every difference in a Change Log. Frontend and QA must be able to build from this file alone.

## Technical Notes
PO choice 2026-10-26 for VULN-012: the refresh token is an HttpOnly cookie. Do not document a CSP alternative.

### Cookie session (breaks Sprint 02 login, refresh, logout)
- Cookie name `delivery_refresh`. `Path=/api/v1/auth/`. `HttpOnly`. `SameSite=Strict`. `Secure` when env `REFRESH_COOKIE_SECURE` is true (development default false, production default true). `Max-Age` equals the refresh lifetime (still 7 days unless env overrides it).
- `POST /auth/token/` 200 body keeps `data.access` and `data.user` and **drops `data.refresh`**. The cookie is set instead.
- `POST /auth/token/refresh/` takes **no** JSON body. The cookie is the credential. 200 body is `data.access` only. The cookie is rotated (old token blacklisted). A JSON `refresh` field is ignored.
- `POST /auth/logout/` takes **no** JSON body. The cookie is the credential. 200 is idempotent (missing, expired, or already blacklisted cookie still 200) and the cookie is cleared.
- Refresh and logout require an `Origin` header that is one of `CORS_ALLOWED_ORIGINS`. Missing or foreign Origin is 403 `code: origin_rejected`. No tokens are issued or rotated in that case.
- CORS must allow credentials. The allowed origin stays an explicit list, never `*`.
- Reuse of a blacklisted refresh cookie returns 401, blacklists every outstanding refresh token of that user, and clears the cookie (VULN-017).
- `Cache-Control: no-store` on every `/api/v1/auth/` response (VULN-019).
- Access token stays in memory on the client. It is still valid until it expires (15 minutes) after logout, password change, or deactivation. Say that in the contract.

### New auth endpoints
- `POST /auth/password/change/` — bearer auth. Body `{ "current_password", "new_password" }`. Wrong current password is 400 `errors.current_password`. Weak new password is 400 `errors.new_password` (same validators as registration). Success 200, cookie cleared, all of that user's refresh tokens blacklisted. Only while logged in.
- `PATCH /auth/me/` — bearer auth. Body may include `full_name`, `phone`, `email` only. `role`, `status`, or `username` in the body is 400. Phone stays unique and normalised (8–15 digits). Email is optional, lower-cased, and unique among non-empty emails (database constraint, VULN-018). Success returns the same user object as `GET /auth/me/`.
- `POST /auth/password/reset/` — no auth. Body `{ "identifier" }` (phone, username, or email). **Always** 200 with the same body and similar timing, whether the account is missing, has no email, or was emailed. No account enumeration. A single-use token, 30-minute lifetime, is emailed only when the account exists, is not soft-deleted, and has an email. Dev uses the console email backend; the token is never in the JSON response.
- `POST /auth/password/reset/confirm/` — no auth. Body `{ "token", "new_password" }`. Unknown, expired, or reused token is the same 400. Weak password is 400 `errors.new_password`. Success 200, token burned, all of that user's refresh tokens blacklisted.
- Recovery throttle: new scope `recovery`, default `5/hour` per IP and `5/hour` per normalised identifier (env). 429 uses the standard body. The standing UI line "if you have no email, contact an administrator" is frontend copy, not a distinct API error (BL-016's identical-response rule wins).

### Account status
Add `rejected` beside `pending_approval`, `active`, `deactivated`. Rejected accounts cannot log in. After a correct password, login returns 403 `code: account_rejected` (same timing rule as the other 403s: wrong password stays a generic 401). The message may include the stored reason. Do not reuse `deactivated` for rejection.

### User management (Admin and Manager only)
Prefix `/api/v1/users/`. Permission: operational Admin or Manager. Manager may see Admin rows but every write against an Admin target is 403 with a clear message (BR-14). Use `can_manage_account` in `apps/users/permissions.py`. Paginate lists with the Sprint 01 shape (`count`, `next`, `previous`, `results`).

| Method | Path | Rule |
|--------|------|------|
| GET | `/users/?role=&status=&search=` | All users. `search` matches name or phone. Filters are exact. |
| GET | `/users/{id}/` | Profile fields plus `rejection_reason` and `last_action` (`action`, `reason`, `actor_id`, `actor_name`, `created_at`, or null). |
| POST | `/users/` | Create. Fields: `full_name`, `phone`, `username`, `email`, `password`, `role`. Role is `admin`, `manager`, `driver`, `trader`, or `client`. Manager cannot send `role: admin`. New accounts are `active` (staff-created, not self-registered). |
| PATCH | `/users/{id}/` | Edit name, phone, username, email, and optionally `password` and `role`. A password set here revokes that user's refresh tokens. Manager cannot change an Admin or set `role: admin`. |
| DELETE | `/users/{id}/` | Soft delete. Cannot delete yourself (400). Manager cannot delete an Admin (403). |
| POST | `/users/{id}/approve/` | Only from `pending_approval`, and only driver or trader. Sets `active`. |
| POST | `/users/{id}/reject/` | Body `{ "reason" }` optional. Only from `pending_approval`. Sets `rejected` and stores the reason. |
| POST | `/users/{id}/activate/` | Only from `deactivated` to `active`. |
| POST | `/users/{id}/deactivate/` | Only from `active` to `deactivated`. Blacklists that user's refresh tokens. |

Each approve, reject, activate, and deactivate writes one `AccountAction` row (who, when, action, optional reason). That is the whole audit for this sprint. There is no public audit-list API (BL-069 is Sprint 10).

Orders do not exist yet. The contract states that deactivating a driver must not cancel a future assigned order, and that a pending or rejected driver cannot be assigned and a pending or rejected trader is not shown to clients. No order endpoints in this sprint.

### Hardening to document (implemented in TASK-053)
- Login `username_or_phone` max length 150, `password` max length 128. Longer input is 400, not a hash (VULN-015).
- An identifier is normalised as a phone only when every character is a digit, space, dash, `+`, bracket, or Arabic-Indic digit. Otherwise it is an exact username match. If both could match, the exact username wins (VULN-016).
- Deep or invalid JSON is 400. A body over the upload limit is 413. A weird `user_id` claim is 401, not 500 (VULN-014). Nginx body size stays DevOps.

### Login codes
| `code` | When |
|--------|------|
| `account_pending` | unchanged |
| `account_deactivated` | unchanged |
| `account_rejected` | new |
| `origin_rejected` | refresh or logout Origin check failed |

## Acceptance Criteria
- [x] `docs/sprints/sprint-03/API_CONTRACT.md` exists and covers every endpoint above with request, success, and error examples
- [x] The Change Log says the refresh token left the JSON body
- [x] Frontend and QA can work from the contract alone
- [x] No application code in this task

## Activity Log
- 2026-10-26 — team_leader: Task created. PO chose the HttpOnly refresh cookie for VULN-012.
- 2026-10-26 — backend: Wrote `docs/sprints/sprint-03/API_CONTRACT.md`. Refresh token is the `delivery_refresh` cookie (`HttpOnly`, `SameSite=Strict`, `Path=/api/v1/auth/`). Login, refresh, and logout no longer carry `data.refresh`. New endpoints: password change, profile patch, password reset, and `/users/` including approve, reject, activate, deactivate. New status `rejected` and codes `account_rejected`, `origin_rejected`, `admin_protected`. No application code in this task. Status IN_REVIEW.
- 2026-10-26 — product owner: Accepted the contract and approved Backend to start TASK-045. Status DONE.
