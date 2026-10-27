# TASK-085: Admin review screen

- **Backlog item:** BL-023
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-081
- **Estimate:** M

## Description
Pending-review list with full details, approve with optional fee, reject with reason.

## Technical Notes
- See the description.

## Acceptance Criteria
- [x] Approve and reject work against the contract (mocked)
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /admin/orders/review (OrderReviewView): created orders with reference, client and phone, shop or direct, pickup, delivery, items and details; approve with optional fee (validated 0 to 100000, 2 decimals, sent as a number) or reject with a required reason; row removed on success; a 400 (already reviewed) refreshes the queue; admin nav link. en and ar. 12 new tests; Vitest 376 passed, eslint clean, vite build ok. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
