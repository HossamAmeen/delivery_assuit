# TASK-082: Client shops list and shop details screens

- **Backlog item:** BL-045, BL-046
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-079
- **Estimate:** M

## Description
Routes `/client/shops` and `/client/shops/:id` with search, empty state, and the shop's items.

## Technical Notes
- See the description.

## Acceptance Criteria
- [x] Screens work against the contract (mocked)
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /client/shops (search by name with a short pause, paging, empty/error/offline states) and /client/shops/:id (items, price only where set, 404 shown as 'not available', link to the order screen), src/api/shops.js and src/api/orders.js, client nav link, and the home shop entry is now a link. en and ar. 10 new tests; Vitest passes, eslint clean. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
