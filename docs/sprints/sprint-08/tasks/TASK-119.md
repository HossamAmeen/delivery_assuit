# TASK-119: Client order details, tracking and cancel

- **Backlog item:** BL-050, BL-025
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-118, TASK-102
- **Estimate:** L

## Description
Route `/client/orders/:id` with status message, driver name, timeline, cancel while allowed.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Cancel only before assignment
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /client/orders/:id (ClientOrderView): status message (waiting for review / waiting for a driver), driver name after assignment (no phone), items with prices, fee, timeline, refresh; cancel (optional reason, asks first) and edit link only while created or available; a refused cancel reloads the real state. en and ar. 12 tests; Vitest 494 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
