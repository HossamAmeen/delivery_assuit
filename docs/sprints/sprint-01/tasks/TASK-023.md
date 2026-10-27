# TASK-023: QA end-to-end: Docker environment and CI pipeline

- **Backlog item:** BL-003
- **Assignee:** qa
- **Status:** DONE (Docker part; CI deferred)
- **Depends on:** TASK-018, TASK-020
- **Estimate:** M

## Description
Review BL-003 Docker files by reading only (Docker is not run; PO decision 2026-10-08). CI (BL-004) is deferred; skip CI cases.

## Technical Notes
- Cases: follow the README only on a clean checkout and reach a running system with one command; frontend reaches backend inside containers (Healthy shown); DB data persists across `docker compose down`/`up` (volumes kept); `.env.example` has no secrets and every variable is documented; compose config validates; CI runs backend and frontend jobs on a push/PR, fails visibly on a deliberately failing test and a lint error.
- Record results in `QA_REPORT.md`; file BUG-XXX for failures.

## Acceptance Criteria
- [x] README-only fresh start verified (followed the README on a clean .env; see notes)
- [x] Persistence and container networking verified; CI failure behavior NOT verified (CI deferred, TASK-019/020)
- [x] BUG-XXX filed for failures (BUG-002..005, all fixed)

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — qa: BLOCKED by PO decision (2026-10-10): Docker not run, CI deferred. Unverified criteria listed in QA_REPORT.md. Static checks only.
- 2026-10-10 — qa: Unblocked by PO ("run it once"). Docker part executed; results in QA_REPORT.md. CI cases remain skipped (deferred).
- 2026-10-10 — qa: BUG-006 (admin login redirect to /accounts/profile/ 404) found by a strict README run; fixed with LOGIN_REDIRECT_URL, verified in Chrome.
