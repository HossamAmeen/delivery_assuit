# TASK-053: Auth hardening batch

- **Backlog item:** BL-012, BL-064; VULN-014, VULN-015, VULN-016, VULN-019
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-045
- **Estimate:** M

## Description
Close the four Low auth findings that Sprint 02 left open. No new product behaviour beyond what the contract already describes.

## Technical Notes
- **VULN-019.** Middleware or a view mixin: every response under `/api/v1/auth/` gets `Cache-Control: no-store`. Cover login, refresh, logout, register, me, password change, and both recovery endpoints.
- **VULN-015.** `LoginSerializer`: `username_or_phone` max length 150, `password` max length 128. Over-long input is 400 and must not call the password hasher.
- **VULN-016.** In `authenticate_user` / phone helpers: normalise to a phone only when the identifier's characters are all digits, spaces, dashes, `+`, brackets, or Arabic-Indic digits. Otherwise compare the trimmed string to `username` exactly. When the string is a plausible phone and also equals a username, the username match wins.
- **VULN-014.** In `common/exception_handler.py`, map a JSON parse that raises `RecursionError` to 400, `RequestDataTooBig` (and the `SuspiciousOperation` subclass it uses) to 413, and a non-integer `user_id` claim in `StatusCheckingJWTAuthentication` to 401. No stack trace in the body. The generic 500 body stays for everything else.
- Nginx `client_max_body_size` is not this task. Deploy is still deferred.
- Update the contract Change Log if a status code here is more specific than TASK-044 wrote.

## Acceptance Criteria
- [x] Auth responses include `Cache-Control: no-store`
- [x] A 2 MB password is 400 and does not run the hasher
- [x] `x01000000005` does not authenticate as phone `01000000005`
- [x] A deeply nested JSON array and an over-size body do not return 500
- [x] A signed access token with a non-integer `user_id` returns 401
- [x] Tests written and passing

## Activity Log
- 2026-10-26 — team_leader: Task created from the Sprint 03 hardening batch in SPRINT.md.
- 2026-10-27 — backend: VULN-019 `NoStoreMiddleware` sets `Cache-Control: no-store` on `/api/v1/auth/` and also `/api/v1/users/` (personal data). VULN-015 login `username_or_phone` max 150 and `password` max 128; a 2 MB password is 400 and neither hasher runs. VULN-016 login matches an exact username first, and a phone only when every character is a digit, space, dash, `+` or bracket (any script), so `x01000000005` no longer logs in as `01000000005`; password recovery lookup follows the same rule. VULN-014 `SafeJSONParser` turns deep nesting into a ParseError; the handler maps every ParseError to 400 `errors.non_field_errors: ["Invalid JSON."]`, `RequestDataTooBig` to 413, other `SuspiciousOperation` to 400, and the auth class refuses a signed token whose `user_id` is not an integer (401). simplejwt 5.5 stores the id as a string, so a plain digit string (up to 18 digits) counts as an integer. Everything else keeps the generic 500 body (tested). 23 new tests; full suite 535 passed, 1 skipped, three clean runs; ruff clean. Note: one earlier full run failed `test_parallel_refresh_yields_exactly_one_success` once (SQLite lock timing, the documented limit) and passed on every rerun. Status IN_REVIEW. Not QA-tested (QA paused by PO).
