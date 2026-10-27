# TASK-114: Orders summary counts

- **Backlog item:** BL-040
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-113
- **Estimate:** S

## Description
`GET /orders/summary/`.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Counts match the list for each role
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built GET /orders/summary/ (total, waiting_review, waiting_for_driver, in_progress, delivered, cancelled) over the caller's visible orders; counts add up and match the list for each role; trader never counts unreviewed orders. 6 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
