# TASK-117: Trader dashboard counts

- **Backlog item:** BL-040
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-114
- **Estimate:** S

## Description
Counts on the trader home.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Counts shown for total, waiting, in progress, delivered, cancelled
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built TraderHomeView as the /trader home (keeps title, name and role): counts from GET /orders/summary/ (all, waiting for a driver, in progress, delivered, cancelled) that add up to the total, empty message at zero orders, error/offline retry, link to the orders. getSummary in orders API; role-home spec mocks it. en and ar. 5 tests; Vitest 478 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
