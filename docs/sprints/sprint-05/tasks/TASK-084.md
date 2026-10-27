# TASK-084: Direct delivery screen

- **Backlog item:** BL-048
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-080
- **Estimate:** M

## Description
Pickup, delivery (type or saved address), details, notes, confirmation with reference.

## Technical Notes
- See the description.

## Acceptance Criteria
- [x] Pickup, delivery, details are required
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /client/direct (DirectDeliveryView): pickup and delivery each by saved address or typed place (PlaceChooser), required details (3 to 1000), confirmation with the reference, server errors on the right side, no double submit. Client home 'Deliver from place to place' entry is now a link (both entries live). en and ar. 9 new tests; Vitest 361 passed. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
