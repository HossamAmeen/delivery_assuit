# TASK-126: Client rates the driver

- **Backlog item:** BL-051
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-123
- **Estimate:** M

## Description
Rating form on a delivered order, once.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built the rating form on /client/orders/:id: shown only on a delivered, unrated order (score 1 to 5, optional comment), once rated it shows the rating instead; refused repeat reloads the real state; no double send. orders API rateOrder, getMyPerformance, getDashboard, listDriverPerformance. en and ar. 12 tests; Vitest 525 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
