# TASK-092: Admin assign screen

- **Backlog item:** BL-031
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-089
- **Estimate:** M

## Description
Route `/admin/orders/assign`: available orders, a driver picker showing busy drivers as unavailable, assign action.

## Technical Notes
- See the description.

## Acceptance Criteria
- [x] Assign works and removes the row; busy driver cannot be chosen
- [x] Server errors shown
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /admin/orders/assign (OrderAssignView): available orders, driver picker listing busy drivers as disabled with the order that keeps them busy, assign, row removed, drivers reloaded; driver errors on the field, stale-order 400 refreshes the queue; admin nav link; orders API gets listDrivers, assignOrder, advanceOrder, getOrder. en and ar. 11 new tests; Vitest 387 passed. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
