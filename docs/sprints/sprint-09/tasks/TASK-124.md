# TASK-124: Driver performance calculation, driver endpoint and staff overview

- **Backlog item:** BL-062, BL-063, BL-060
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-123
- **Estimate:** L

## Description
Numbers per month with month-boundary tests.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Known sample data matches
- [x] Driver sees aggregates only
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built orders/performance.py (three queries, month key from the delivery time, cancellation time and the rating's order delivery time in the server time zone) with GET /drivers/me/performance/?month= (aggregates only, months list for the picker, zeros for a new driver) and GET /staff/drivers/performance/?month=&ordering=delivered|rating (paginated, unrated last on rating). Month-boundary, time-zone and wrong-driver tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
