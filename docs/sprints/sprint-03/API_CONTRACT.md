# API Contract — Sprint 03 (Account management)

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-014, BL-015, BL-016, BL-052, BL-059, BL-064, BL-078 | **Task:** TASK-044
- **Status:** DRAFT for implementation. Contract first; any change goes through the Team Leader and is recorded in the Change Log.
- **Builds on:** `../sprint-02/API_CONTRACT.md`. The Sprint 01 envelope, `/api/v1/` prefix, `Accept-Language`, pagination, and the 400/401/403/404/405/429/500 bodies still apply. This file lists only what Sprint 03 changes or adds.
- **PO decision (2026-10-26):** the refresh token moves to an HttpOnly cookie (VULN-012). It is no longer in any JSON body.

Frontend and QA build against this document only. Until the tasks below are implemented, the running server still follows the Sprint 02 contract.

## What changed from Sprint 02
| Endpoint | Change |
|----------|--------|
| `POST /auth/token/` | `data.refresh` is removed. A `delivery_refresh` cookie is set instead. Login identifier rules are stricter (VULN-015, VULN-016). New 403 `account_rejected`. |
| `POST /auth/token/refresh/` | No JSON body. The cookie is the credential. `data.refresh` is removed. `Origin` is required. Reuse revokes every refresh token of that user. |
| `POST /auth/logout/` | No JSON body. The cookie is the credential. `Origin` is required. Still idempotent. |
| `GET /auth/me/` | Adds `rejection_reason`. |
| `PATCH /auth/me/` | New. |
| `POST /auth/password/change/` | New. |
| `POST /auth/password/reset/` | New. |
| `POST /auth/password/reset/confirm/` | New. |
| `/users/` | New. |

Every response under `/api/v1/auth/`, success or error, sends `Cache-Control: no-store` (VULN-019).

Access and refresh lifetimes are unchanged: access 15 minutes (`JWT_ACCESS_TOKEN_LIFETIME_MINUTES`), refresh 7 days (`JWT_REFRESH_TOKEN_LIFETIME_DAYS`).

## Concepts

### Refresh cookie
| Attribute | Value |
|-----------|--------|
| Name | `delivery_refresh` |
| Value | the refresh JWT |
| `Path` | `/api/v1/auth/` |
| `HttpOnly` | yes (not visible to `document.cookie`) |
| `SameSite` | `Strict` |
| `Secure` | yes when `REFRESH_COOKIE_SECURE` is true. Development default **false**. Production default **true**. |
| `Max-Age` | the refresh lifetime, in seconds |
| `Domain` | omitted (host-only) |

The browser stores the cookie. The frontend never reads or writes it. API calls that must carry it use credentials (`axios` `withCredentials: true`). `CORS_ALLOW_CREDENTIALS` is true. `CORS_ALLOWED_ORIGINS` stays an explicit list and is never `*`.

`localhost` with two ports (Vite `5173`, API `8000`) is one site, so `SameSite=Strict` still sends the cookie on those API calls. The page origin must be in `CORS_ALLOWED_ORIGINS`.

A JSON field named `refresh` on login, refresh, or logout is **ignored**. There is one credential channel: the cookie.

The access token stays in JSON (`data.access`) and in memory only. After logout, password change, password reset, or deactivation it keeps working until it expires (at most 15 minutes). The next protected call by a deactivated account is still 403 `account_deactivated`, because status is checked on every request. The frontend discards the access token immediately on those events.

### Origin check
`POST /auth/token/refresh/` and `POST /auth/logout/` require an `Origin` header whose value is exactly one entry of `CORS_ALLOWED_ORIGINS` (scheme, host, and port).

Missing or any other value:

```json
{ "success": false, "message": "This request's origin is not allowed.", "errors": {}, "code": "origin_rejected" }
```

HTTP 403. The cookie is not rotated and nothing is blacklisted. Login, registration, and password reset do **not** require `Origin`.

### Account status
| Value | Meaning | Can log in / use the API |
|-------|---------|--------------------------|
| `pending_approval` | Driver or trader self-registered, waiting | No |
| `active` | Normal account | Yes |
| `deactivated` | Blocked by Admin/Manager (BL-052) | No |
| `rejected` | Driver or trader registration refused (BL-078) | No |

`rejected` is not `deactivated`. Pending and rejected accounts are not activated or deactivated; they are approved or rejected.

Self-registration is unchanged: driver and trader → `pending_approval`, client → `active`. Accounts created by Admin/Manager (below) are `active`, including drivers and traders.

A pending or rejected driver must not be assigned an order. A pending or rejected trader must not be shown to clients. Those screens do not exist yet. No order or shop endpoint is added here.

### Error `code`
| `code` | HTTP | When |
|--------|------|------|
| `account_pending` | 403 | Unchanged. Correct password, status `pending_approval`. |
| `account_deactivated` | 403 | Unchanged. Correct password, or a still-valid access token, status `deactivated`. |
| `account_rejected` | 403 | Correct password, status `rejected`. No token. |
| `origin_rejected` | 403 | Refresh or logout `Origin` check failed. |
| `admin_protected` | 403 | A Manager tried to create, edit, delete, approve, reject, activate, or deactivate an Admin (BR-14). |

Clients branch on `code` or HTTP status, never on message text. English messages below are the `en` copy. Arabic comes from `Accept-Language: ar` and is owned by the backend catalogues.

### User objects
- **Login summary** (unchanged shape): `{ "id", "full_name", "role", "status" }`. `status` here is always `active`.
- **Profile** (`GET` and `PATCH /auth/me/`): `{ "id", "full_name", "phone", "username", "email", "role", "status", "rejection_reason" }`. `username` is JSON `null` when unset. `email` and `rejection_reason` are `""` when unset.
- **List row** (`GET /users/`): `{ "id", "full_name", "phone", "username", "email", "role", "status" }`.
- **Managed user** (`GET /users/{id}/` and the body of create, patch, approve, reject, activate, deactivate): the profile fields plus

```json
"last_action": {
  "action": "approved",
  "reason": "",
  "actor_id": 1,
  "actor_name": "Demo Admin",
  "created_at": "2026-10-26T12:00:00Z"
}
```

`last_action` is `null` when nothing has been recorded. `action` is `approved`, `rejected`, `activated`, or `deactivated`. `created_at` is ISO-8601 UTC. Passwords, hashes, `is_staff`, and `is_superuser` are never returned.

### Phone, username, email
- Phone input may contain spaces, dashes, `+`, brackets, and Arabic-Indic digits. Stored form is ASCII digits, 8 to 15 of them. Unique.
- **Login identifier (VULN-016).** If every character is a digit, space, dash, `+`, bracket, or Arabic-Indic digit, it is a phone and is normalised. Otherwise it is a username and is matched exactly (case-sensitive, surrounding spaces trimmed). `x01000000005` does **not** match phone `01000000005`. If the raw trimmed value equals a username and also looks like a phone, the username account wins.
- Email is optional. Stored lower-cased and trimmed. Unique among non-empty emails, including case (`A@X.com` and `a@x.com` are one address). Many empty emails are allowed. Duplicate message: `A user with this email already exists.`
- Passwords use the Sprint 02 validators. The field key is `password`, `new_password`, or whatever the endpoint lists. Max length on login is 128 (VULN-015). Registration max length stays 128.

### Who may call what
"Operational" means authenticated and status `active`.

| Action | Anonymous | Client, trader, driver | Manager | Admin |
|--------|:---------:|:----------------------:|:-------:|:-----:|
| Register, login | ✔ | ✔ | ✔ | ✔ |
| Refresh, logout | ✔ (cookie + Origin) | ✔ | ✔ | ✔ |
| Password reset request and confirm | ✔ | ✔ | ✔ | ✔ |
| `GET`/`PATCH /auth/me/`, change own password | 401 | ✔ own row | ✔ | ✔ |
| `GET /users/`, `GET /users/{id}/` | 401 | 403 | ✔ sees Admins too | ✔ |
| Create / edit / delete / approve / reject / activate / deactivate an **Admin** | 401 | 403 | **403 `admin_protected`** | ✔ |
| Those writes on any other role | 401 | 403 | ✔ | ✔ |

```json
{ "success": false, "message": "You cannot manage an administrator account.", "errors": {}, "code": "admin_protected" }
```

### Throttling
| Endpoint | Scope | Default env | Default rate |
|----------|-------|-------------|--------------|
| `register/*` | `sensitive` | `RATELIMIT_SENSITIVE` | 30/minute per IP |
| `token/`, `token/refresh/`, `logout/`, `password/change/` | `auth` for the public ones; change uses `user` | `RATELIMIT_AUTH`, `RATELIMIT_USER` | 10/minute per IP; 300/minute per user |
| `GET`/`PATCH /auth/me/` | `user` | `RATELIMIT_USER` | 300/minute per user |
| `password/reset/`, `password/reset/confirm/` | `recovery` | `RATELIMIT_RECOVERY_IP`, `RATELIMIT_RECOVERY_IDENTIFIER` | 5/hour per IP **and** 5/hour per normalised identifier |
| `/users/` | `user` | `RATELIMIT_USER` | 300/minute per user |

Either recovery limit returns the standard 429 with `Retry-After`. The identifier key is the trimmed, lower-cased string, after phone normalisation when the value looks like a phone.

### Bodies that are not 500 (VULN-014)
| Input | HTTP | Body |
|-------|------|------|
| JSON that cannot be parsed, including nesting deep enough to raise `RecursionError` | 400 | `{ "success": false, "message": "Validation failed.", "errors": { "non_field_errors": ["Invalid JSON."] } }` |
| Body over Django's upload limit (`RequestDataTooBig`) | 413 | `{ "success": false, "message": "Request body is too large.", "errors": {} }` |
| A signed access token whose `user_id` claim is not an integer | 401 | standard 401 body |

Nginx `client_max_body_size` is not part of this contract. No stack trace is ever returned.

---

## POST /api/v1/auth/token/  (changed)
Log in with phone or username.
- **Auth:** none. Scope `auth`. No `Origin` requirement.
- **Request:** `{ "username_or_phone": "string", "password": "string" }`.
  - `username_or_phone` required, max length **150**.
  - `password` required, max length **128**.
  - Over-long input is 400 and the password hasher is not run.
- **200:**
  ```json
  {
    "success": true,
    "message": "Login successful.",
    "data": {
      "access": "<jwt>",
      "user": { "id": 12, "full_name": "Ahmed Ali", "role": "driver", "status": "active" }
    }
  }
  ```
  Response header `Set-Cookie` sets `delivery_refresh` as specified above. There is no `data.refresh`.
- **400:** missing, blank, or over-long field. `errors.username_or_phone` / `errors.password`. Over-long uses Django's max-length message (`Ensure this field has no more than 150 characters.` / `... 128 characters.`).
- **401:** wrong password, unknown identifier, or soft-deleted account. Same body and similar timing for all of these:
  ```json
  { "success": false, "message": "Invalid credentials.", "errors": {} }
  ```
- **403** only after the password was verified. No cookie and no access token.
  ```json
  { "success": false, "message": "Your account is pending approval. You will be able to log in once an administrator approves it.", "errors": {}, "code": "account_pending" }
  ```
  ```json
  { "success": false, "message": "Your account has been deactivated. Please contact the administrator.", "errors": {}, "code": "account_deactivated" }
  ```
  ```json
  { "success": false, "message": "Your registration was rejected.", "errors": {}, "code": "account_rejected" }
  ```
  When a rejection reason is stored, the message is `Your registration was rejected. Reason: <reason>.` The reason is plain text from the admin, shown as part of `message` only.
- **429:** standard.
- **Task:** TASK-045 (cookie), TASK-049 (`account_rejected`), TASK-053 (lengths and identifier rule)

## POST /api/v1/auth/token/refresh/  (changed)
Rotate the refresh cookie and return a new access token.
- **Auth:** cookie `delivery_refresh`. Header `Origin` as above. Scope `auth`. No bearer required.
- **Request body:** empty. A `refresh` property is ignored.
- **200:**
  ```json
  { "success": true, "message": "Token refreshed successfully.", "data": { "access": "<jwt>" } }
  ```
  `Set-Cookie` replaces `delivery_refresh`. The previous refresh token is blacklisted.
- **401:** missing cookie, invalid, expired, logged out, reuse, or the account is not `active` (pending, rejected, deactivated, or deleted):
  ```json
  { "success": false, "message": "Token is invalid or expired.", "errors": {} }
  ```
  **Reuse** (the cookie's token is already blacklisted): same 401, and every outstanding refresh token of that user is blacklisted. The cookie is cleared.
  A database lock error on rotation is also this 401, never 500. Two parallel refreshes of the same token produce at most one 200. The strict "exactly one 200" check on PostgreSQL is Sprint 02 E1 and is not required to ship this sprint.
- **403:** `origin_rejected`. Cookie unchanged.
- **429:** standard.
- **Task:** TASK-045

## POST /api/v1/auth/logout/  (changed)
- **Auth:** cookie. Header `Origin`. Scope `auth`. Works after the access token has expired.
- **Request body:** empty. Ignored if present.
- **200** even when the cookie is missing, expired, or already blacklisted:
  ```json
  { "success": true, "message": "Logged out successfully.", "data": {} }
  ```
  The cookie is cleared (`Max-Age=0`). A valid token is blacklisted.
- **403:** `origin_rejected`. Cookie left as it was.
- **429:** standard.
- **Task:** TASK-045

## GET /api/v1/auth/me/  (changed)
- **Auth:** `Authorization: Bearer <access>`. Scope `user`. Permission: operational user; the row is always the caller.
- **200:** profile object under `data.user`, now including `rejection_reason`.
- **401 / 403:** unchanged (403 is `account_deactivated` when a still-valid token belongs to a deactivated account).
- **Task:** TASK-047, TASK-049 (`rejection_reason`)

## PATCH /api/v1/auth/me/
Update the caller's own name, phone, and email.
- **Auth:** bearer. Scope `user`. Operational caller only.
- **Request:** any subset of `{ "full_name", "phone", "email" }`.
  - `full_name`: 2–255, trimmed.
  - `phone`: normalised, unique, 8–15 digits.
  - `email`: optional. `""` clears it. Otherwise a valid address, stored lower-cased, unique when non-empty.
- If `role`, `status`, or `username` is present, **400 and no field is saved**:
  ```json
  { "success": false, "message": "Validation failed.", "errors": { "role": ["You cannot change this field."] } }
  ```
  One entry per forbidden key that was sent.
- **200:** the same profile object as GET, under `data.user`. Message: `Profile updated.`
- **400:** field errors. Phone and email duplicates use the registration messages (`A user with this phone number already exists.`, `A user with this email already exists.`).
- **Task:** TASK-047

## POST /api/v1/auth/password/change/
- **Auth:** bearer. Scope `user`. Operational caller only. This is the only way a user changes their own password (BR-9).
- **Request:**
  ```json
  { "current_password": "old-password", "new_password": "S0me-Strong-Pass" }
  ```
  Both required. `new_password` uses the shared validators. Max length 128.
- **200:**
  ```json
  { "success": true, "message": "Password changed. Please log in again.", "data": {} }
  ```
  Every refresh token of this user is blacklisted. `delivery_refresh` is cleared. No new access token and no new cookie. The old password no longer logs in.
- **400:**
  ```json
  { "success": false, "message": "Validation failed.", "errors": { "current_password": ["Current password is incorrect."] } }
  ```
  A weak `new_password` is `errors.new_password` (the validator messages). The stored password is unchanged.
- **401 / 403:** standard. A wrong current password is 400, not 401.
- **Task:** TASK-046

## POST /api/v1/auth/password/reset/
Ask for a reset email. The response does not reveal whether the account exists.
- **Auth:** none. Scope `recovery`.
- **Request:** `{ "identifier": "01001234567" }` (phone, exact username, or email). Required, max length 254. Blank is 400 `errors.identifier`.
- **200 for every identifier that parses**, including unknown, soft-deleted, no email on file, and emailed:
  ```json
  { "success": true, "message": "If an email is on file for that account, a reset link has been sent.", "data": {} }
  ```
  Timing is similar for the unknown path and the sent path.
- An email is sent only when the account exists, is not soft-deleted, and `email` is non-empty. The message contains one link: `{FRONTEND_ORIGIN}/reset-password?token=<raw>`. `FRONTEND_ORIGIN` default `http://localhost:5173`. The raw token is never in the JSON body. Only a hash is stored. Lifetime is `PASSWORD_RESET_TIMEOUT_MINUTES` (default **30**). A newer request invalidates the previous unused token for that user.
- Development mail backend is the console backend. Tests read the locmem outbox. No real SMTP server is required.
- The screen, not this endpoint, always shows: if the account has no email, contact an administrator.
- **429:** standard, after 5 requests in an hour per IP or per identifier.
- **Task:** TASK-048

## POST /api/v1/auth/password/reset/confirm/
- **Auth:** none. Scope `recovery`.
- **Request:**
  ```json
  { "token": "<raw token from the link>", "new_password": "S0me-Strong-Pass" }
  ```
- **200:**
  ```json
  { "success": true, "message": "Password has been reset. Please log in.", "data": {} }
  ```
  The token is burned. The new password works and the old one does not. Every refresh token of that user is blacklisted. The cookie is cleared when the request brought one. No access token is issued.
- **400** unknown, expired, or already used token (one message, so they cannot be told apart):
  ```json
  { "success": false, "message": "Validation failed.", "errors": { "token": ["This reset link is invalid or has expired."] } }
  ```
- **400** weak `new_password`: `errors.new_password` with the validator messages. A token that was still valid **stays valid**.
- **429:** standard.
- **Task:** TASK-048

## GET /api/v1/users/
- **Auth:** bearer. Operational Admin or Manager. Scope `user`.
- **Query:** `page` (default 1), `page_size` (default 20, max 100), `role`, `status` (exact match on the enums above), `search` (case-insensitive contains on `full_name` or `phone` only).
- **200:** Sprint 01 pagination envelope. `results` are list rows. Order is newest `id` first. Soft-deleted users are omitted. A Manager's list **includes** Admin rows.
- **401** anonymous. **403** any other role (standard permission message, no `code`).
- **Task:** TASK-051

## GET /api/v1/users/{id}/
- **Auth:** bearer. Operational Admin or Manager.
- **200:** `data.user` is a managed user.
- **404:** unknown id or soft-deleted user. Standard 404 body.
- **403:** a non-admin role. A Manager **may** read an Admin.
- **Task:** TASK-051

## POST /api/v1/users/
Staff creates an account that is immediately `active`.
- **Auth:** bearer. Operational Admin or Manager.
- **Request:**
  ```json
  {
    "full_name": "Sara Nabil",
    "phone": "0100 999 8877",
    "username": "sara",
    "email": "sara@example.com",
    "password": "S0me-Strong-Pass",
    "role": "manager"
  }
  ```
  | Field | Required | Rules |
  |-------|:--------:|-------|
  | `full_name` | yes | 2–255, trimmed |
  | `phone` | yes | normalised, unique |
  | `username` | required when `role` is `admin` or `manager`; otherwise optional | unique, max 150 |
  | `email` | no | unique when non-empty, stored lower-cased |
  | `password` | yes | shared validators, max 128 |
  | `role` | yes | `admin`, `manager`, `driver`, `trader`, or `client` |
- `status`, `is_staff`, and `is_superuser` in the body are 400 (`You cannot change this field.`) and nothing is created. Status is always `active`.
- Manager sending `role: admin` is 403 `admin_protected` and nothing is created.
- **201:** `data.user` is the managed user (`last_action` null). Message: `User created.`
- **400:** field errors, same phone and email messages as registration.
- **Task:** TASK-052

## PATCH /api/v1/users/{id}/
- **Auth:** bearer. Operational Admin, or a Manager when `can_manage_account` allows the target.
- **Request:** any subset of `full_name`, `phone`, `username`, `email`, `password`, `role`. Same rules as create. Omitted `password` leaves the password. `""` for `password` is 400. A non-empty `password` sets it and blacklists that user's refresh tokens.
- `status`, `is_staff`, `is_superuser` in the body are 400 and nothing is saved. Status changes go through the action endpoints.
- Manager targeting an Admin, or sending `role: admin`, is 403 `admin_protected` and nothing is saved.
- **200:** `data.user` managed user. Message: `User updated.`
- **404:** unknown or soft-deleted.
- **Task:** TASK-052

## DELETE /api/v1/users/{id}/
Soft-delete (`deleted_at` set). The user can no longer log in.
- **Auth:** bearer. Same write permission as PATCH.
- **200:**
  ```json
  { "success": true, "message": "User deleted.", "data": {} }
  ```
- **400** when the target is the caller:
  ```json
  { "success": false, "message": "Validation failed.", "errors": { "non_field_errors": ["You cannot delete your own account."] } }
  ```
- **403** `admin_protected` when a Manager targets an Admin.
- **404:** unknown or already soft-deleted.
- **Task:** TASK-052

## POST /api/v1/users/{id}/approve/
- **Auth:** bearer. Admin or Manager, and `can_manage_account`.
- **Request body:** empty.
- Only a driver or trader whose status is `pending_approval`. Otherwise 400 and no `AccountAction` row:
  ```json
  { "success": false, "message": "Validation failed.", "errors": { "status": ["Only a pending driver or trader can be approved."] } }
  ```
- **200:** managed user with `status: "active"`, `rejection_reason: ""`, `last_action.action: "approved"`. Message: `User approved.`
- **Task:** TASK-049

## POST /api/v1/users/{id}/reject/
- **Auth:** same as approve.
- **Request:** `{ "reason": "Missing documents" }`. `reason` is optional, max 500 characters, stored trimmed. Omit or `""` for no reason.
- Same pending driver/trader rule. Otherwise 400 `errors.status`: `Only a pending driver or trader can be rejected.` Nothing is written.
- **200:** `status: "rejected"`, `rejection_reason` set, `last_action.action: "rejected"`. Message: `User rejected.`
- **Task:** TASK-049

## POST /api/v1/users/{id}/activate/
- **Auth:** same write permission.
- Only from `deactivated` to `active`. Otherwise 400 `errors.status`: `Only a deactivated account can be activated.` Pending and rejected accounts are unchanged.
- **200:** `last_action.action: "activated"`. Message: `User activated.` Old refresh tokens are not restored.
- **403** `admin_protected` for a Manager targeting an Admin.
- **Task:** TASK-050

## POST /api/v1/users/{id}/deactivate/
- **Auth:** same write permission.
- Only from `active` to `deactivated`. Otherwise 400 `errors.status`: `Only an active account can be deactivated.`
- The caller cannot deactivate themselves:
  ```json
  { "success": false, "message": "Validation failed.", "errors": { "non_field_errors": ["You cannot deactivate your own account."] } }
  ```
- **200:** `last_action.action: "deactivated"`. Message: `User deactivated.` Every refresh token of the target is blacklisted. Their current access token fails the next protected call with `account_deactivated`.
- Deactivating a driver must not cancel or unassign an order. Orders are not in this sprint; the rule is recorded for the order sprint.
- **Task:** TASK-050

Each approve, reject, activate, and deactivate writes one `AccountAction` (target user, actor, action, reason, time). There is no list-all-actions endpoint (that is BL-069, Sprint 10). `last_action` is the latest row.

## Registration (unchanged, restated where Sprint 03 tightens it)
`POST /auth/register/{driver,trader,client}/` is unchanged: no tokens, no cookie, role from the URL. Email uniqueness is now also a database constraint; the 400 message stays `A user with this email already exists.`

## Task cross-reference
| Concern | Task |
|---------|------|
| This contract | TASK-044 |
| Cookie, Origin, reuse | TASK-045 |
| Change password | TASK-046 |
| Profile edit, unique email | TASK-047 |
| Password recovery | TASK-048 |
| Approve / reject, `rejected` | TASK-049 |
| Activate / deactivate | TASK-050 |
| Users list and detail | TASK-051 |
| Create, edit, delete | TASK-052 |
| Lengths, identifier rule, 400/413, `Cache-Control` | TASK-053 |
| Frontend cookie session | TASK-054 |
| Frontend screens | TASK-055..062 |
| QA | TASK-063, TASK-064 |

## Out of scope
Phone OTP, CSP, order assignment, shop visibility, the full audit log (BL-069), Nginx body size, PostgreSQL concurrency proof (Sprint 02 E1), and the VULN-013 outside-host retest (Sprint 02 E2). No deploy.

## Change Log
| Date | Change | By |
|------|--------|----|
| 2026-10-26 | Initial Sprint 03 contract. Refresh token leaves JSON for the `delivery_refresh` cookie. | backend |
| 2026-10-27 | TASK-048 settings: throttle scopes `recovery` and `recovery_identifier` (env `RATELIMIT_RECOVERY`, `RATELIMIT_RECOVERY_IDENTIFIER`, default `5/hour` each); env `FRONTEND_ORIGIN`, `PASSWORD_RESET_TIMEOUT_MINUTES`, `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`. A phone identifier is matched only when it looks like a phone (digits and `+ - ( )` and spaces only). | backend |
| 2026-10-27 | TASK-049..053 details: `no-store` also applies to `/api/v1/users/`. A signed token's `user_id` counts as an integer when it is an int or a plain digit string (simplejwt stores strings). Any request-body parse error is 400 `Invalid JSON.`. `PATCH /users/{id}/`: nobody can change their own `role` (400 `errors.role`, `You cannot change your own role.`); `username` is required for admin and manager and a blank username clears it for other roles. `GET /users/?search=` matches the phone only when the text is digit-like. Create/patch username error: `A user with this username already exists.`. `GET /users/{id}/` for a pending or rejected account works like any other. | backend |
