# TASK-090: Driver execution: advance an order

- **Backlog item:** BL-032
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-089
- **Estimate:** M

## Description
`POST /orders/{id}/advance/` moves assigned, picked up, in delivery, delivered, in that order only, by the assigned driver only.

## Technical Notes
- Calls lifecycle.transition; the server chooses the next step

## Acceptance Criteria
- [x] Only the assigned driver can advance; others 403 or 404
- [x] No step can be skipped or repeated past delivered
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built POST /orders/{id}/advance/ (orders/execute.py): the server picks the next step (assigned, picked up, in delivery, delivered), driver only, another driver's order is 404, a fourth tap and cancelled orders are 400 with no new history row. 19 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
