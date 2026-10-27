# TASK-089: Assign an order to a driver, and the drivers list

- **Backlog item:** BL-031
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-081
- **Estimate:** L

## Description
`POST /orders/{id}/assign/` and `GET /drivers/` for Admin and Manager, with BR-1, BR-3 and concurrency rules.

## Technical Notes
- Lock the order row and the driver row in one transaction
- Assignment goes through lifecycle.transition

## Acceptance Criteria
- [x] Only available orders and active drivers; busy driver refused
- [x] Two parallel assignments: exactly one wins
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built POST /orders/{id}/assign/ (orders/assign.py: lock the order, then the driver, in one transaction; only available orders, only active drivers, BR-1 busy driver refused, history row with actor and time) and GET /drivers/ (active drivers with has_active_order and active_order_reference, ?available=). Staff only. Arabic messages added. 21 tests including double assignment of one order and two orders to one driver. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
