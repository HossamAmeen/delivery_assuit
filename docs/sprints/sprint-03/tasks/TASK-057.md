# TASK-057: Password recovery screens

- **Backlog item:** BL-016
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-054
- **Estimate:** M

## Description
From login, a person can ask for a reset email and then set a new password with the link they received.

## Technical Notes
- Public routes: `/forgot-password` (`forgot-password`) and `/reset-password` (`reset-password`). Both are guest-looking pages; `/reset-password` stays reachable even if a session exists, because the email link must open.
- Login screen gets a "Forgot password?" link.
- Request form: one field `identifier` (phone, username, or email). Submit calls `POST /auth/password/reset/`. Always show the same success text the API returns, plus a fixed line in both languages: if the account has no email, contact an administrator. Do not branch on whether the account exists.
- Confirm form: read `token` from the query string. Fields: new password, confirm. Submit `POST /auth/password/reset/confirm/` with `{ token, new_password }`. Missing token shows an error and no request. Server 400 shows the message. Success goes to login.
- Rate-limit 429 shows the standard message and does not look like a validation error.
- No token is written to localStorage.

## Acceptance Criteria
- [x] Login links to the request screen
- [x] The request screen shows the same confirmation for any identifier
- [x] The contact-an-administrator sentence is always visible on that screen
- [x] Opening `/reset-password?token=...` and submitting a matching password calls the confirm endpoint
- [x] A missing token does not call the API
- [x] Vitest covers both screens

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-016.
- 2026-10-27 — frontend: Public routes `/forgot-password` and `/reset-password` (not guest-only, so the email link opens even with a session). Login has a Forgot password link and shows a notice after a reset. Request screen: one identifier field, shows the API's confirmation text unchanged for any identifier and always shows the contact-an-administrator sentence; 429 is a form message, not a field error. Reset screen: token from the query string (never stored), new password plus confirm; a missing token shows an error and sends nothing; a server link error shows as the form error, a weak password on the field; success goes to login. Arabic and English strings added. 12 new Vitest tests; suite 211 passed; eslint clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
