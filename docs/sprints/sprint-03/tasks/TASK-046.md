# TASK-046: Change password and revoke sessions

- **Backlog item:** BL-014; VULN-017 (password-change half)
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-045
- **Estimate:** M

## Description
A logged-in user changes their own password. The old password stops working. Every refresh token for that user is revoked.

## Technical Notes
- `POST /api/v1/auth/password/change/` as in the contract. Permission `IsOperational`. Throttle scope `user`.
- Service function, not serializer logic: verify `current_password` with the hasher, run Django's password validators on `new_password`, save, then blacklist every outstanding refresh token for that user and clear `delivery_refresh`.
- Wrong current password is 400 on `current_password` and does not reveal anything else. Same validators and bilingual messages as registration.
- The current access token is not denylisted (it dies within 15 minutes). The response does not issue a new access token or a new cookie. The client will send the user to login.
- No email is sent. This is not recovery.

## Acceptance Criteria
- [x] Anonymous callers get 401; a deactivated account gets 403 `account_deactivated`
- [x] Wrong current password and a weak new password are rejected and the password is unchanged
- [x] After success the new password logs in and the old one does not
- [x] Outstanding refresh tokens for that user return 401, and the cookie is cleared
- [x] Tests written and passing

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-014.
- 2026-10-27 — backend: `POST /auth/password/change/` added (`IsOperational`, global `user` throttle). Logic in `services.change_password`: checks the current password, runs the shared validators, saves, then blacklists every outstanding refresh token of that user in one transaction. The view clears `delivery_refresh` and returns no access token. Arabic strings added to `locale/ar` and compiled. 16 new tests; full suite 314 passed; ruff clean. Status IN_REVIEW. QA has not tested it yet.
