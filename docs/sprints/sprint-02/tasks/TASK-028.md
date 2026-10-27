# TASK-028: User model: account status field and registration rules

- **Backlog item:** BL-008, BL-009, BL-010, BL-011
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-027
- **Estimate:** M

## Description
Extend the User model with an account status and the data registration needs.

## Technical Notes
- Add `status` (`pending_approval` | `active` | `deactivated`), default `active`. Driver and Trader registrations create `pending_approval`; Client creates `active`; Admin/Manager are `active`.
- `full_name` required for self-registered users (Trader: shop/trader name goes in `full_name`); `phone` required for registered users, unique (already unique, nullable only for Admin/Manager created by command). Normalise phone to digits (strip spaces, `+`, dashes) in one helper used by registration and login. `username` stays optional/unique.
- Migration with data-safe default for existing rows (`active`). Update admin to show/filter status. Add `is_operational` helper (active and not deleted).
- Do not allow role or status to be set by anyone but Admin/Manager services (no serializer exposes them).

## Acceptance Criteria
- [x] Migration applies on a database with existing users; existing users become `active`
- [x] Phone normalisation covered by unit tests (spaces, +20, dashes, Arabic-Indic digits)
- [x] Tests written and passing; ruff clean
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-12 — backend: Implemented. Added `User.status` (default active) and `is_operational`; username now nullable+unique; `apps/users/phone.py` `normalize_phone`/`is_valid_phone` used by manager, login (`authenticate_user`) and `create_admin`; migration `0002_user_status` (existing rows become active, phones normalised where no collision); admin lists/filters status; seeder sets status. Tests added (test_phone.py, test_models.py). Status set to IN_REVIEW. Role/status are not exposed by any serializer. Login status checks (403 codes) are left to TASK-031.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results" (backend, TASK-039 APPROVED 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
