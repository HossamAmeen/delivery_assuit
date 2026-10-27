# TASK-099: Item prices by staff and price snapshot on order lines

- **Backlog item:** BL-077
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-098
- **Estimate:** M

## Description
`PATCH /staff/items/{id}/`, price audit fields, `unit_price` on order lines, `items_total`.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Only staff set prices
- [x] Past orders keep their prices
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built PATCH /staff/items/{id}/ (staff only, 0 to 100000 or null, price_set_by and price_set_at), OrderItem.unit_price snapshot at creation, line price and items_total in the order object. Migrations shops 0003, orders 0002. Trader endpoint still cannot set a price. Tests incl. past orders keep their price. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
