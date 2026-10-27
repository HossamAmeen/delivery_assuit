# TASK-080: Create order: shop order and direct delivery

- **Backlog item:** BL-047, BL-048
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-077, TASK-079, TASK-069
- **Estimate:** L

## Description
`POST /orders/` for active clients. Validation, saved-address resolution (own only), place snapshots, items with quantities, status `created`, history row.

## Technical Notes
- Whole create in one transaction
- Exactly-one-of rules for place objects vs saved addresses
- Shop must be orderable at the moment of creation

## Acceptance Criteria
- [x] Both scenarios create a `created` order with a reference
- [x] Missing items, delivery place, or description (direct) block creation with field errors
- [x] Another client's saved address is rejected
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built POST /api/v1/orders/ (clients only; same URL as the list). One serializer for both scenarios: shop order (shop, optional pickup_location, items with quantities, optional description, delivery place or saved address) and direct delivery (pickup, delivery, required details). Places copied into the order; another client's saved address gives the same error as a missing one; shop must be orderable at that moment; fee, status and driver cannot be sent; one transaction with the first history row. Arabic messages added. 40 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
