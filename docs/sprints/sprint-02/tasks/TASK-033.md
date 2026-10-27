# TASK-033: seed_demo: demo accounts per role and status

- **Backlog item:** BL-007 (follow-up), BL-009, BL-012
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-030
- **Estimate:** S

## Description
Keep demo data useful now that statuses exist (the approval screen only arrives in Sprint 03).

## Technical Notes
- Seed one active Driver and one active Trader (approved) so demos work, plus one `pending_approval` Driver and one `deactivated` Client to demo the messages. Still idempotent; passwords from `DEMO_PASSWORD`.
- Update README and tests.

## Acceptance Criteria
- [x] Running twice creates no duplicates
- [x] Each status is represented
- [x] Tests written and passing
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-15 — backend: Added demo_driver_pending (pending_approval) and demo_client_deactivated (deactivated) to users seeder; driver/trader already active. Tests + README updated; 291 backend tests pass, ruff clean. Status IN_REVIEW.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results" (backend, TASK-039 APPROVED 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
