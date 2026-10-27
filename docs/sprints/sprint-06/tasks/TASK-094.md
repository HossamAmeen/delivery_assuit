# TASK-094: Driver order details and next-step button

- **Backlog item:** BL-030, BL-032
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-091
- **Estimate:** M

## Description
Route `/driver/orders/:id`: full details, contact phones, and the single valid next action.

## Technical Notes
- See the description.

## Acceptance Criteria
- [x] Only the one valid action is shown
- [x] Button is disabled while the request runs
- [x] Delivered shows no action
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /driver/orders/:id (DriverOrderView): reference, status, pickup, delivery, details, items, shop and client with phones as call links only when the server sent them (none for finished orders), assigned and delivered times, cancel reason, and only the one valid next-action button (none once delivered); a 404 reads 'not available to you'; a refused step reloads the order. en and ar. 10 tests; Vitest 409 passed. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
