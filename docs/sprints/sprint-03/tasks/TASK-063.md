# TASK-063: Backend QA for Sprint 03

- **Backlog item:** BL-014, BL-015, BL-016, BL-052, BL-059, BL-064, BL-078; VULN-012, VULN-014..019
- **Assignee:** qa
- **Status:** TODO
- **Depends on:** TASK-045, TASK-046, TASK-047, TASK-048, TASK-049, TASK-050, TASK-051, TASK-052, TASK-053
- **Estimate:** M

## Description
Test the Sprint 03 API against the contract and the backlog acceptance criteria. Do not fix code. File bugs as `BUG-XXX` and send failures back to the Team Leader.

## Technical Notes
- No local Docker. Use the backend venv and a live dev server, same as Sprint 02.
- Read `docs/sprints/sprint-03/API_CONTRACT.md` and `docs/backlog/BACKLOG.md` for BL-014, BL-015, BL-016, BL-052, BL-059, BL-064, BL-078.
- Suite: `pytest` must pass and new-code coverage must be at least 80%. Also run a black-box script against the live server.
- Cookie cases: login sets `delivery_refresh` with `HttpOnly` and `SameSite=Strict`; the JSON body has no refresh token; refresh rotates the cookie; logout clears it; a missing Origin on refresh is 403 and does not rotate; a replayed old cookie is 401 and kills the user's other refresh tokens.
- Password: wrong current password, weak new password, success then old password fails, refresh tokens die.
- Profile: own row only; role and status rejected; duplicate email including case difference; empty email allowed.
- Recovery: same 200 body for unknown, no-email, and emailed accounts; token single use; weak password does not consume a valid token; throttle 429; after reset, old refresh tokens fail.
- Approval: pending driver and trader; rejected login code only after the right password; action row written.
- Activate and deactivate: manager versus admin is 403; deactivated user cannot log in; refresh tokens die. Do not require an order fixture.
- Users: list filters and search; manager cannot create, edit, or delete an admin; admin can; soft delete cannot log in.
- Hardening: over-long login password is 400; a junk-prefixed phone does not match; deep JSON is not 500; auth responses send `Cache-Control: no-store`.
- N-14: hit the live user endpoints as each role, not only the test URLconf.
- PostgreSQL (E1) and the VULN-013 outside-host retest (E2) are still out of scope. Record them as not run.

## Acceptance Criteria
- [ ] `docs/sprints/sprint-03/QA_REPORT.md` exists (backend section) with pass/fail per task
- [ ] Every backlog acceptance check above is marked pass or filed as a bug
- [ ] No code fixes by QA

## Activity Log
- 2026-10-26 — team_leader: Task created.
