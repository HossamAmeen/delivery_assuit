# TASK-107: Admin orders table

- **Backlog item:** BL-054
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-101
- **Estimate:** M

## Description
Route `/admin/orders`: all orders with filters (status, period, reference search), paging, row opens details.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Columns per BL-054
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /admin/orders (OrdersTableView): all orders table with reference (link to details), client, shop, driver, pickup, delivery, status, fee, created; filters status, created from/to, reference search (short pause, back to page 1); paging; empty/error/offline retry; nav link 'All orders'; src/api/staff.js and setFee/cancelOrder in orders.js. en and ar. 6 tests; Vitest 424 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
