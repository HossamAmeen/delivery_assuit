# TASK-095: Driver My Orders (history)

- **Backlog item:** BL-034
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-091
- **Estimate:** S

## Description
Route `/driver/orders`: delivered and cancelled orders, paginated, opens the details.

## Technical Notes
- See the description.

## Acceptance Criteria
- [x] Newest first with reference, status, dates
- [x] Pagination works
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /driver/orders (DriverHistoryView): delivered and cancelled orders from ?scope=history, newest first as the server returns them, reference, status badge, delivered or cancelled date, details link, paging, empty and error/offline retry. en and ar. 6 tests; Vitest 415 passed. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
