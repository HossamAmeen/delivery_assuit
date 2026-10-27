# TASK-052: Create, edit, and delete users

- **Backlog item:** BL-059; BR-14
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-045, TASK-051
- **Estimate:** M

## Description
Admin creates, edits, and deletes Admin and Manager accounts. Manager does the same for Manager accounts and for drivers, traders, and clients, and is refused for Admin accounts.

## Technical Notes
- `POST`, `PATCH`, and `DELETE /api/v1/users/` and `/api/v1/users/{id}/` as in the contract.
- Enforce `can_manage_account` on the target. Creating `role: admin` is allowed only when the actor is Admin. A Manager's attempt is 403 with a clear message, and no row is written.
- Create sets `status` to `active` and `is_staff` true only for Admin (match `create_admin` / seed). Password is required and uses the shared validators. Phone and username uniqueness use the existing rules. Email uses TASK-047's normalised unique email.
- PATCH cannot set `status` (that is approve / reject / activate / deactivate). Optional `password` replaces the password and blacklists that user's refresh tokens.
- A Manager cannot change a target's role to `admin`, and cannot edit any field of an Admin.
- DELETE sets `deleted_at` (the project's soft delete). Deleted users fail login the way they do today. Deleting yourself is 400. Manager deleting an Admin is 403.
- Do not allow a payload to set `is_superuser` or `is_staff` directly.

## Acceptance Criteria
- [x] Admin can create, edit, and delete an Admin and a Manager
- [x] Manager can create, edit, and delete a Manager, driver, trader, and client
- [x] Manager cannot create, edit, or delete an Admin, and the 403 body is explicit
- [x] Setting a password on PATCH revokes that user's refresh tokens
- [x] Soft-deleted users cannot log in
- [x] Tests written and passing, including a test that names BR-14

## Activity Log
- 2026-10-26 — team_leader: Task created for the write side of BL-059.
- 2026-10-27 — backend: `POST /users/`, `PATCH /users/{id}/`, `DELETE /users/{id}/` added. Create makes an `active` account; `is_staff` and `is_superuser` are true only for Admin (same as `create_admin` and the seeder); `username` is required for admin and manager. A Manager sending `role: admin`, or targeting an Admin, gets 403 `admin_protected` before any change. `status`, `is_staff`, `is_superuser` in the body are 400. PATCH password validates, sets, and blacklists the user's refresh tokens; `""` is 400; a blank username clears it except for admin and manager. DELETE soft-deletes, revokes refresh tokens, refuses self-delete (400), and the old access token then gets 401. Phone and username of a deleted user stay reserved (DB unique). Added one rule the task did not list: nobody can change their own role (400), so the last Admin cannot demote themself. Tests name BR-14. Arabic strings added. 71 new tests; full suite green; ruff clean; `makemigrations --check` clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
