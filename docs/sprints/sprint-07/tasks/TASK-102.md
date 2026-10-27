# TASK-102: Cancel order

- **Backlog item:** BL-025, BL-055
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-098
- **Estimate:** M

## Description
`POST /orders/{id}/cancel/` for the owning client (before assignment) and staff (any unfinished).

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Rules of BR-12 enforced
- [x] Driver freed on cancel
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built POST /orders/{id}/cancel/: owning client before assignment (reason optional), staff any unfinished order (reason 3 to 500 required), final orders 400, driver freed and shown in history, no driver release. Tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
