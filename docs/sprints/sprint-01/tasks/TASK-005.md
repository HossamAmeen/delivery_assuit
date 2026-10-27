# TASK-005: Minimal custom User model, manager and users app

- **Backlog item:** BL-007
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-003
- **Estimate:** M

## Description
Create the `users` app with a minimal custom user model so the first Admin can exist. `AUTH_USER_MODEL` must be set before the first migration. Roles/permissions are extended later by BL-008 (SEC-02); do not build registration, approval, or role-based permissions here.

## Technical Notes
- `apps/users/models.py`: `User(AbstractBaseUser, PermissionsMixin, BaseModel)` with `username` (unique), `phone` (unique, nullable), `email` (optional), `full_name`, `role` (choices Admin, Manager, Driver, Trader, Client; default Client), `is_active`, `is_staff`. Login identifier = phone OR username (Q4); email optional (Q5).
- `managers.py`: `UserManager` with `create_user` and `create_superuser` (role=Admin). Driver (not Worker) naming everywhere.
- Register in Django admin (Jazzmin). Add initial migration.
- Keep the model minimal: only fields BL-007 needs; flag in the Activity Log any field you expect BL-008 to change.

## Acceptance Criteria
- [x] User can be created via manager; username and phone uniqueness enforced; email optional
- [x] Migration committed; `makemigrations --check` clean
- [x] Model, manager and serializer-free tests pass; coverage >= 80%
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-08 — backend: Implemented apps/users (User, UserManager, admin, 0001_initial), AUTH_USER_MODEL=users.User. Status IN_REVIEW. check, makemigrations --check, ruff check, make test (59 passed) all clean; apps/users coverage 99%. Notes for BL-008: `role` stored as lowercase values (admin/manager/driver/trader/client); `phone` blank is normalised to NULL; `email` optional and non-unique; default manager hides soft-deleted users (login blocked), `all_objects` shows all. Fields BL-008 may change: role, is_active (approval state), possibly email uniqueness.
- 2026-10-10 — qa: TASK-021 backend QA PASS (see QA_REPORT.md); status DONE.
