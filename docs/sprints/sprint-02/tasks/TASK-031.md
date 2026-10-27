# TASK-031: Login update: status checks and user summary

- **Backlog item:** BL-012
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-028, TASK-029
- **Estimate:** M

## Description
Extend `POST /auth/token/` for Sprint 02 rules without weakening Sprint 01 protections.

## Technical Notes
- Wrong credentials still return the generic 401 (`Invalid credentials.`) with equal timing. Status is only revealed AFTER the password is verified: `pending_approval` -> 403 `{code: account_pending}`, `deactivated` -> 403 `{code: account_deactivated}` with friendly bilingual messages; no tokens issued.
- Success response adds `user` (id, full_name, role, status) next to `access` and `refresh`, so the frontend can route to the role's home without another call.
- Failed-attempt limits stay: `auth` throttle and the existing behaviour; add a test that a pending/deactivated account cannot be probed without the correct password.
- Keep login by phone (normalised) or username.

## Acceptance Criteria
- [x] Pending and deactivated accounts get distinct, friendly messages only with the correct password
- [x] Invalid credentials never reveal whether the phone/username exists (body and timing)
- [x] Response contains the user summary
- [x] Tests written and passing; Sprint 01 auth tests updated, not deleted
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-12 — backend: Implemented. services.ensure_can_login runs only after the password is verified (403 account_pending/account_deactivated, no tokens); login data now includes user {id, full_name, role, status}; 401 path, auth throttle and dummy-hash timing unchanged. Tests added in apps/users/tests/test_auth.py (Sprint 01 tests updated, none deleted). Added backend/conftest.py with MD5 hasher for tests (test_timing keeps the real hasher). Full suite 276 passed, ruff clean. Status -> IN_REVIEW.
- 2026-10-16 — security: Reviewed. VULN-015, VULN-016 (login length/identifier normalisation) relate to this task; see ../SECURITY_REPORT.md.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results" (backend, TASK-039 APPROVED 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
