# TASK-029: Role permission classes and /auth/me/

- **Backlog item:** BL-008
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-028
- **Estimate:** M

## Description
Implement role-based access once, reusable by every later sprint, and a first protected endpoint that proves it.

## Technical Notes
- `common/permissions.py` or `apps/users/permissions.py`: `IsAdmin`, `IsAdminOrManager`, `IsDriver`, `IsTrader`, `IsClient`, plus `IsOperational` (status `active`). Denied -> 403 envelope.
- Policy helper `can_manage_account(actor, target)`: Admin may manage anyone; Manager may manage everyone except Admin accounts (BR-14). Used by later user-management sprints; unit-test it now.
- `GET /api/v1/auth/me/` (authenticated, any status): returns id, full_name, phone, username, email, role, status. Unauthenticated -> 401 envelope.
- Add a small test-only view set (not in production URLs) or parametrised tests that check each role allowed/denied on at least one protected action (acceptance criterion BL-008). Unauthenticated users can only reach register, login, refresh and (later) recovery.

## Acceptance Criteria
- [x] Each role is allowed and denied on at least one protected action
- [x] Manager is denied on Admin accounts via `can_manage_account`
- [x] Unauthenticated access to `/auth/me/` returns the 401 envelope
- [x] Tests written and passing; coverage >= 80% on new code
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-12 — backend: Implemented. `apps/users/permissions.py` (IsOperational, IsAdmin, IsAdminOrManager, IsDriver, IsTrader, IsClient, `can_manage_account`), `apps/users/authentication.py` (`StatusCheckingJWTAuthentication`, set as default auth class: re-checks status on every request, deactivated -> 403 `account_deactivated`, pending -> 403 `account_pending`), `apps/users/exceptions.py`, optional `code` in the error envelope (`common/responses.py`, `exceptions.py`, `exception_handler.py`), `GET /api/v1/auth/me/` (`MeView`, OpenAPI documented). Tests in `apps/users/tests/test_permissions.py` (role matrix via test-only URLconf, can_manage_account, /me 200/401/403). No migrations. Status -> IN_REVIEW.
- 2026-10-12 — backend: PO decision recorded: pending accounts do NOT get access to `/auth/me/` (pending -> 403 `account_pending`, deactivated -> 403 `account_deactivated`). Current behaviour kept; no code change. Note: the task text "authenticated, any status" is superseded by this decision. (Login never issues tokens to pending accounts anyway.)
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results" (backend, TASK-039 APPROVED 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
