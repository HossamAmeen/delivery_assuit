# TASK-115: Edit an order before assignment

- **Backlog item:** BL-026
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-113
- **Estimate:** L

## Description
`PATCH /orders/{id}/` with re-review of available orders.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] BR-13 boundary tested for every status and role
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built PATCH /orders/{id}/ (orders/edit.py): owning client or staff, only while created or available (client after assignment 403, staff 400 on status), shop orders edit description, pickup_location, items (price re-snapshot), delivery; direct orders edit description, pickup, delivery; same validation as creation; editing an available order sends it back to review (new lifecycle move available to created, reason 'edited'). 25 tests incl. the BR-13 boundary for every status and role; suite 1077 passed, 1 skipped. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
