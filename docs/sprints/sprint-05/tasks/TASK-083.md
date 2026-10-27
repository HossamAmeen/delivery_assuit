# TASK-083: Order from a shop screen

- **Backlog item:** BL-047
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-080, TASK-082
- **Estimate:** L

## Description
Item picker with quantities, pickup choice, delivery place (type or saved address), note, confirmation with reference.

## Technical Notes
- See the description.

## Acceptance Criteria
- [x] Blocks on missing items or delivery place
- [x] Shows the reference after success
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /client/shops/:id/order (OrderFromShopView): quantity per item (0 means not ordered), default or chosen pickup, delivery place by saved address or typed (new shared PlaceChooser and choice helpers in utils/places), optional note, confirmation with the order reference. Blocks on missing items or delivery place; server errors on the matching field; closed shop shown as a page message; no double submit. en and ar. 16 new tests; Vitest 352 passed. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
