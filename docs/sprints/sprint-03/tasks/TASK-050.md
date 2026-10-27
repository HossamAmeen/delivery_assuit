# TASK-050: Activate and deactivate accounts

- **Backlog item:** BL-052; VULN-017 (deactivation half)
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-045, TASK-049
- **Estimate:** M

## Description
Admin or Manager sets a non-admin account active or deactivated. A deactivated user cannot log in or call the API. Their refresh tokens die immediately.

## Technical Notes
- `POST /api/v1/users/{id}/activate/` and `POST /api/v1/users/{id}/deactivate/` as in the contract.
- Activate only from `deactivated`. Deactivate only from `active`. Pending and rejected accounts are 400 (those go through TASK-049).
- Manager targeting an Admin is 403 (BR-14), including an Admin who is somehow deactivated.
- Deactivate blacklists every outstanding refresh token of the target and writes `AccountAction` `deactivated`. The target's current access token still works until it expires, but `IsOperational` already returns 403 `account_deactivated` on the next request. Add a test for that.
- Activate writes `AccountAction` `activated` and does not restore old refresh tokens.
- Orders do not exist. Do not invent an order table. The service docstring states that a later order sprint must leave assigned orders in place when a driver is deactivated. Acceptance here is the account status and the token revoke only.
- A user cannot deactivate themselves through this endpoint (400). Staff use another Admin.

## Acceptance Criteria
- [x] Active becomes deactivated and deactivated becomes active, with an `AccountAction` row each time
- [x] A deactivated user cannot log in and cannot call `GET /auth/me/` with an old access token (403)
- [x] That user's refresh tokens fail after deactivation
- [x] Manager receives 403 when the target is an Admin; a driver receives 403 always
- [x] Pending and rejected accounts are unchanged by these two endpoints
- [x] Tests written and passing

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-052. The "active order stays assigned" rule is recorded only; orders are Sprint 05.
- 2026-10-27 — backend: `POST /users/{id}/activate/` and `/deactivate/` added in `admin_services`/`admin_views`. Activate only from `deactivated`, deactivate only from `active` (pending and rejected are 400 and unchanged). Deactivate blacklists all refresh tokens of the target, writes `AccountAction`, and refuses self-deactivation (400). Activate does not restore old tokens. A Manager targeting an Admin (active or deactivated) is 403 `admin_protected` (BR-14 named in the test). The old access token gets 403 `account_deactivated` on the next call (tested). The service docstring records that a later order sprint must leave assigned orders in place. Arabic strings added. 20 new tests; users suite green; ruff clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
