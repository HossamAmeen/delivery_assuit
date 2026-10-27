# TASK-078: Order visibility and read endpoints

- **Backlog item:** BL-024
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-077
- **Estimate:** M

## Description
`GET /orders/` and `GET /orders/{id}/` scoped per role as in the contract, with `?status=` filter and the order serializer (client phone for staff only).

## Technical Notes
- Scoping happens in one queryset helper
- Trader visibility uses the history (approved at least once)
- Unseen order is 404

## Acceptance Criteria
- [x] Each role sees only what the contract allows, tested against another role's order
- [x] Client phone appears for Admin/Manager only
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built apps/orders/visibility.visible_orders (the only read path: client own, trader only orders approved at least once for their shop, driver assigned only, staff all), OrderSerializer (client phone for Admin and Manager only, driver without phone), GET /api/v1/orders/ with ?status= and GET /api/v1/orders/{id}/ (404 when not visible). 20 tests against each role and another role's order. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
