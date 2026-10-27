# API Contract — Sprint 02 (Accounts)

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-008..BL-013 | **Task:** TASK-027
- **Status:** DRAFT, still what the running server does. Login, refresh, and logout JSON in this file are superseded by `../sprint-03/API_CONTRACT.md` once TASK-045 is implemented (PO 2026-10-26: refresh token moves to an HttpOnly cookie). Until then, implementers of Sprint 02 behaviour follow this file.
- **Builds on:** `../sprint-01/API_CONTRACT.md`. Everything there still applies (envelope, `/api/v1/` prefix, `Accept-Language`, throttling, 400/401/403/404/405/429/500 bodies, pagination). Only differences and additions are listed here.

## What changed from Sprint 01
| Endpoint | Change |
|----------|--------|
| `POST /auth/token/` | Success now also returns `data.user`. New 403 responses for pending and deactivated accounts (with `code`). |
| `POST /auth/token/refresh/` | Refresh tokens now **rotate**: the response contains a new `data.refresh`; the old one stops working. Refresh fails for accounts that are no longer active. |
| `POST /auth/register/{driver,trader,client}/` | New. |
| `POST /auth/logout/` | New. |
| `GET /auth/me/` | New. |

Access token lifetime default becomes **15 minutes** (env `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`); refresh token 7 days (env `JWT_REFRESH_TOKEN_LIFETIME_DAYS`). Clients must not hard-code these.

## Concepts

### Roles (`role`)
`admin`, `manager`, `driver`, `trader`, `client`. Exactly one per account. Never chosen or changed by the account holder.

### Account status (`status`)
| Value | Meaning | Can log in / use the API |
|-------|---------|--------------------------|
| `pending_approval` | Driver or Trader registered, waiting for Admin/Manager approval (approval screen arrives in Sprint 03) | No |
| `active` | Normal account | Yes |
| `deactivated` | Blocked by Admin/Manager | No |

Registration sets: Driver → `pending_approval`; Trader → `pending_approval`; Client → `active`. Admin and Manager accounts are `active`.

The server checks the status on **every** protected request, not only at login. A valid access token of an account that was deactivated afterwards gets `403` with `code: "account_deactivated"`.

### Error `code` (new, optional field)
Some errors carry a machine-readable `code` next to the usual fields so the UI can show a specific screen. Clients branch on `code` (or the HTTP status), never on the message text.
```json
{ "success": false, "message": "…", "errors": {}, "code": "account_pending" }
```
| `code` | HTTP | When |
|--------|------|------|
| `account_pending` | 403 | Correct credentials but status `pending_approval` |
| `account_deactivated` | 403 | Correct credentials (login) or valid token (any protected call) but status `deactivated` |

### User objects
- **Login summary** (`data.user` of login): `{ "id": 7, "full_name": "Ahmed Ali", "role": "driver", "status": "active" }`
- **Registration summary** (`data.user` of register): same as login summary plus `phone`.
- **Profile** (`GET /auth/me/`): `{ "id", "full_name", "phone", "username", "email", "role", "status" }`. `username` and `email` may be `null` / `""` respectively when unset. The password and internal fields are never returned.

### Phone numbers
Input may contain spaces, dashes, `+`, and Arabic-Indic digits (٠١٢٣…). The server normalises to ASCII digits only (e.g. `+20 100-123-4567` → `201001234567`) and stores that. Valid after normalisation: **8 to 15 digits**. Login by phone uses the same normalisation. Responses return the normalised value.

### Passwords
Checked with Django's validators: at least 8 characters, not too common, not entirely numeric, not too similar to the name, phone or email. A weak password gives a 400 with `errors.password` (list of messages, localized).

### Home screen per role (frontend routing, informational)
| Role | Home | Screen name |
|------|------|-------------|
| driver | `/driver` | My Assigned Orders |
| trader | `/trader` | Dashboard |
| client | `/client` | Home |
| admin, manager | `/admin` | Dashboard |

### Permission matrix (BL-008)
"Operational" means authenticated **and** status `active`.

| Action | Anonymous | Client | Trader | Driver | Manager | Admin |
|--------|:---------:|:------:|:------:|:------:|:-------:|:-----:|
| Register (3 endpoints), login, refresh, logout | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `GET /auth/me/` | ✘ 401 | ✔ | ✔ | ✔ | ✔ | ✔ |
| Role-restricted actions (later sprints) | ✘ 401 | only client features | only trader features | only driver features | admin features | admin features |
| Create / edit / delete **Admin** accounts (later sprints) | ✘ | ✘ | ✘ | ✘ | **✘ (BR-14)** | ✔ |
| Create / edit / delete other accounts (later sprints) | ✘ | ✘ | ✘ | ✘ | ✔ | ✔ |

A user of one role calling another role's feature gets `403` (`You do not have permission to perform this action.`). Unauthenticated access to anything not in the first row gets `401`. Only registration, login, refresh and logout (and password recovery, Sprint 03) are reachable without a token.

## Throttling
| Endpoint | Scope | Default |
|----------|-------|---------|
| `register/*` | `sensitive` | 30/minute per client IP |
| `token/`, `token/refresh/`, `logout/` | `auth` | 10/minute per client IP |
| `GET /auth/me/` | `user` | 300/minute per user |

429 body and `Retry-After` as in Sprint 01. The client IP honours `NUM_PROXIES` (forged `X-Forwarded-For` does not help).

---

## POST /api/v1/auth/register/driver/
## POST /api/v1/auth/register/trader/
## POST /api/v1/auth/register/client/
Public self-registration. The role and status come from the URL, never from the body. Sending `role` or `status` in the body is ignored.

- **Auth:** none. Scope `sensitive`.
- **Request** (JSON):
  ```json
  { "full_name": "Ahmed Ali", "phone": "0100 123 4567", "password": "S0me-Strong-Pass", "email": "ahmed@example.com" }
  ```
  | Field | Required | Rules |
  |-------|:--------:|-------|
  | `full_name` | yes | 2–255 characters, trimmed. For **trader** this is the shop/trader name. |
  | `phone` | yes | Normalised, 8–15 digits, unique among all accounts. |
  | `password` | yes | Password rules above. Never returned or logged. |
  | `email` | no | Valid address, unique when given. Needed later for password recovery. |
- **201 (driver / trader):**
  ```json
  {
    "success": true,
    "message": "Registration successful. Your account is pending approval.",
    "data": { "user": { "id": 12, "full_name": "Ahmed Ali", "phone": "01001234567", "role": "driver", "status": "pending_approval" } }
  }
  ```
- **201 (client):** same shape, `message: "Registration successful."`, `role: "client"`, `status: "active"`.
- **No tokens** are returned by registration. A client logs in afterwards. A driver/trader sees the "pending approval" message.
- **400** (field errors, nothing is created):
  ```json
  {
    "success": false,
    "message": "Validation failed.",
    "errors": {
      "full_name": ["This field is required."],
      "phone": ["A user with this phone number already exists."],
      "password": ["This password is too common."],
      "email": ["Enter a valid email address."]
    }
  }
  ```
  Other messages: `phone`: `This field is required.` / `Enter a valid phone number (8 to 15 digits).`; `email`: `A user with this email already exists.`
- **429:** standard.
- **Note (accepted enumeration surface):** the duplicate-phone message tells an attacker that a number is registered. This is required by BL-009..011 and is limited by the `sensitive` throttle.
- **Task:** TASK-030 (model/status: TASK-028)

## POST /api/v1/auth/token/  (changed)
Log in with phone **or** username.
- **Auth:** none. Scope `auth`.
- **Request:** unchanged: `{ "username_or_phone": "string", "password": "string" }`. A phone is normalised as above; a username is matched exactly (case-sensitive, surrounding spaces trimmed).
- **200:**
  ```json
  {
    "success": true,
    "message": "Login successful.",
    "data": {
      "access": "<jwt>",
      "refresh": "<jwt>",
      "user": { "id": 12, "full_name": "Ahmed Ali", "role": "driver", "status": "active" }
    }
  }
  ```
  `data.user.status` is always `active` here (other statuses are refused below).
- **400:** missing or blank field (unchanged).
- **401:** wrong credentials, unknown identifier, or soft-deleted account. **Same body and similar timing for all**, so nothing reveals whether the identifier exists:
  ```json
  { "success": false, "message": "Invalid credentials.", "errors": {} }
  ```
- **403** (only after the password was verified, so this cannot be used to probe accounts):
  ```json
  { "success": false, "message": "Your account is pending approval. You will be able to log in once an administrator approves it.", "errors": {}, "code": "account_pending" }
  ```
  ```json
  { "success": false, "message": "Your account has been deactivated. Please contact the administrator.", "errors": {}, "code": "account_deactivated" }
  ```
  No tokens are issued in either case.
- **429:** standard (`auth` scope). Repeated failed attempts from one IP are limited by it.
- **Task:** TASK-031

## POST /api/v1/auth/token/refresh/  (changed)
Exchange a refresh token for new tokens. Tokens **rotate**.
- **Auth:** none (the refresh token is the credential). Scope `auth`.
- **Request:** `{ "refresh": "<jwt>" }`
- **200:**
  ```json
  { "success": true, "message": "Token refreshed successfully.", "data": { "access": "<jwt>", "refresh": "<jwt>" } }
  ```
  The returned `refresh` replaces the old one, which is blacklisted. Clients **must store the new refresh token every time**. Reusing an old refresh token returns 401.
- **400:** missing `refresh` → `errors: { "refresh": ["This field is required."] }`
- **401:** invalid, expired, already used (rotated), logged out, or the account is no longer active (deactivated, pending, or deleted):
  ```json
  { "success": false, "message": "Token is invalid or expired.", "errors": {} }
  ```
- **429:** standard.
- **Task:** TASK-032

## POST /api/v1/auth/logout/  (new)
End the session on the server by blacklisting the refresh token.
- **Auth:** none. The refresh token in the body is the credential, so logout still works after the access token has expired. Scope `auth`.
- **Request:** `{ "refresh": "<jwt>" }`
- **200** (idempotent; also returned when the token is already blacklisted or expired):
  ```json
  { "success": true, "message": "Logged out successfully.", "data": {} }
  ```
- **400:** missing → `errors.refresh: ["This field is required."]`; not a token at all → `errors.refresh: ["Invalid token."]`.
- After logout the refresh token cannot be used again. The already-issued access token stays technically valid until it expires (at most 15 minutes by default); the frontend discards it immediately.
- **429:** standard.
- **Task:** TASK-032

## GET /api/v1/auth/me/  (new)
The caller's profile.
- **Auth:** `Authorization: Bearer <access>`. Scope `user`.
- **200:**
  ```json
  {
    "success": true,
    "message": "Operation completed successfully.",
    "data": { "user": { "id": 12, "full_name": "Ahmed Ali", "phone": "01001234567", "username": null, "email": "ahmed@example.com", "role": "driver", "status": "active" } }
  }
  ```
- **401:** missing, invalid or expired access token (standard 401 body).
- **403:** token valid but the account was deactivated afterwards: `code: "account_deactivated"` (body as above).
- **429:** standard.
- **Task:** TASK-029

## Arabic example
`Accept-Language: ar` → `{ "success": false, "message": "بيانات الاعتماد غير صحيحة.", "errors": {} }`. Exact Arabic wording is owned by the backend i18n files and is not part of the contract.

## Task cross-reference
| Concern | Task |
|---------|------|
| This contract | TASK-027 |
| Status field, phone normalisation | TASK-028 |
| Role permissions, `/auth/me/` | TASK-029 |
| Registration | TASK-030 |
| Login changes | TASK-031 |
| Logout, rotation, blacklist | TASK-032 |
| Demo seed per status | TASK-033 |
| Frontend auth service/store | TASK-034 |
| Frontend guards, screens | TASK-035..038 |
| QA | TASK-039, TASK-040 |

## Out of scope for Sprint 02
Approving pending accounts (Sprint 03), profile edit, change password, password recovery, user management APIs, any order or shop data.

## Change Log
| Date | Change | By |
|------|--------|----|
| 2026-10-11 | Initial Sprint 02 contract | backend |
