# TASK-049: Approve or reject driver and trader registrations

- **Backlog item:** BL-078
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044
- **Estimate:** M

## Description
Admin and Manager approve or reject a pending driver or trader. The account holder sees that state when they try to log in.

## Technical Notes
- Add `User.Status.REJECTED = "rejected"`. Migration. Login: after the password checks out, `rejected` returns 403 `code: account_rejected`. Wrong password stays the generic 401. Follow `ensure_can_login`.
- Add `rejection_reason` (text, blank default) on User.
- Add model `AccountAction`: FK user, FK actor, `action` (`approved`, `rejected`, `activated`, `deactivated`), `reason` blank, timestamp. This task writes `approved` and `rejected` only. Activate and deactivate are TASK-050.
- `POST /api/v1/users/{id}/approve/` and `POST /api/v1/users/{id}/reject/` as in the contract. Permission `IsAdminOrManager` plus `can_manage_account`. A client, driver, or trader caller gets 403.
- Approve and reject only from `pending_approval`, and only when the target role is driver or trader. Anything else is 400 and writes no row.
- Reject stores the optional reason. Approve clears `rejection_reason`.
- Include `rejection_reason` on `GET /auth/me/` so a future screen can show it. Login of a rejected user does not return a token; the 403 message includes the reason when one is stored.
- Extend `seed_demo` with one pending trader (`demo_trader_pending`) so QA has a second pending account. Do not add a rejected demo user unless it keeps the seeder obvious; a test factory is enough for `rejected`.
- Pending and rejected drivers are not assignable and pending and rejected traders are not public. There is no order or shop API yet. State it in a code comment next to the status check and cover it with a unit test on a small helper (for example `is_publicly_operable`) that later sprints must call. Do not create order models.

## Acceptance Criteria
- [x] Approving a pending driver or trader sets `active` and records who and when
- [x] Rejecting sets `rejected`, stores the optional reason, and records who and when
- [x] A rejected user, with the right password, gets 403 `account_rejected` and no tokens
- [x] A client cannot approve; a manager cannot reject an Admin (no Admin is pending anyway; the permission still holds)
- [x] Calling approve on an active or client account changes nothing
- [x] Tests written and passing

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-078. `rejected` is a new status so it is not confused with `deactivated`.
- 2026-10-27 — backend: Added status `rejected`, `User.rejection_reason`, model `AccountAction`, and migration 0005. `POST /users/{id}/approve/` and `/reject/` (new `admin_*.py` modules; `IsAdminOrManager` plus `can_manage_account`, Manager targeting an Admin is 403 `admin_protected`). Only a pending driver or trader can be approved or rejected; anything else is 400 `errors.status` and writes no row. Login with the right password for a rejected account is 403 `account_rejected` (message includes the reason), no token and no cookie; wrong password stays the generic 401. `GET /auth/me/` returns `rejection_reason`. `seed_demo` adds `demo_trader_pending` (8 demo users; `rejected` is made by test factories). `admin_services.is_publicly_operable` is the helper later order and shop sprints must call (unit tested). Arabic strings added. 31 new tests; full suite green; ruff clean; `makemigrations --check` clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
