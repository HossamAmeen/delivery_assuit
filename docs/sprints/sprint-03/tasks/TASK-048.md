# TASK-048: Password recovery by email

- **Backlog item:** BL-016; VULN-017 (reset half)
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-045, TASK-047
- **Estimate:** M

## Description
A person who forgot their password requests a reset. If that account has an email, a single-use link is sent. The HTTP response is the same when the account does not exist.

## Technical Notes
- `POST /auth/password/reset/` and `POST /auth/password/reset/confirm/` as in the contract.
- Store only a hash of the token (same idea as a password). Raw token goes in the email only. Lifetime 30 minutes. Second request invalidates the previous unused token for that user.
- Email body contains a link to `{FRONTEND_ORIGIN}/reset-password?token=<raw>`. `FRONTEND_ORIGIN` comes from the environment. Development default `http://localhost:5173`.
- Development email backend: console. Tests use locmem (`mail.outbox`). The API response never includes the token.
- Identifier lookup: phone (normalised, and only when it looks like a phone — same rule as VULN-016), exact username, or case-insensitive email. Soft-deleted accounts are treated as unknown.
- Unknown account, account with no email, and successful send all return the same 200 message. Do not answer faster for the unknown path (hash or sleep to the same order of magnitude as a real lookup; follow the existing timing tests' approach).
- Confirm: one use, then the row is marked used. Expired and reused tokens share one 400 message. Success sets the password, burns the token, and blacklists all of that user's refresh tokens.
- Throttle scope `recovery`: `5/hour` per IP and `5/hour` per normalised identifier, both env-driven. Document the env names in the contract if TASK-044 left them generic, via the contract Change Log.
- No phone OTP.

## Acceptance Criteria
- [x] The reset response body is identical for an unknown identifier, an account with no email, and an account that was emailed
- [x] An account with no email is not sent a message
- [x] The link works once; a second confirm fails; a weak password is rejected and does not burn a still-valid token
- [x] After a successful reset the new password works, the old one does not, and old refresh tokens fail
- [x] The sixth request in an hour from one IP is 429
- [x] Tests written and passing

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-016. Identical response wins over a distinct "no email" error; the UI tells the user to contact an administrator.
- 2026-10-27 — backend: `POST /auth/password/reset/` and `/reset/confirm/` added. New model `PasswordResetToken` (migration 0004): only a SHA-256 hash is stored, 30-minute lifetime (`PASSWORD_RESET_TIMEOUT_MINUTES`), a newer request burns the older unused link, and confirm claims the token with one conditional UPDATE so only one caller wins. A weak password is checked before the claim, so it does not burn the token. Success revokes all refresh tokens and clears the cookie only if the request brought one. Lookup: email (case-insensitive), exact username, or a phone only when the text looks like a phone (so `abc0100…` is not matched). All outcomes return the same 200 body; a mail failure is logged and still returns the same 200. Throttles `recovery` (per IP) and `recovery_identifier` (per normalised identifier), both `5/hour`, env `RATELIMIT_RECOVERY` and `RATELIMIT_RECOVERY_IDENTIFIER`. Mail settings added (console in development, locmem in tests; `FRONTEND_ORIGIN`, `EMAIL_*`, `DEFAULT_FROM_EMAIL` in `.env.example`). Arabic strings and Arabic email added. 26 new tests; full suite 365 passed, 1 skipped; ruff clean; `makemigrations --check` clean. Known limit: the email is sent inside the request. With a slow real SMTP server the known-account answer is slower than the unknown one; move sending to Celery before production if that matters (the unknown path builds the same token and message to keep CPU work alike). Status IN_REVIEW. Not QA-tested (PO paused QA).
