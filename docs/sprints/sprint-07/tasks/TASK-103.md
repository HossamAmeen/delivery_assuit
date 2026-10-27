# TASK-103: Trader approval and status effects

- **Backlog item:** BL-043
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-098
- **Estimate:** S

## Description
Tests that pending, rejected, and deactivated traders are blocked and hidden, and staff still see their orders.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Tests only (behaviour already follows from IsOperational, orderable_shops and visible_orders): pending, rejected and deactivated traders cannot log in (account codes), an old token stops working on trader endpoints, the shop leaves the client list and detail, clients cannot order from it, staff still see its orders, reactivation restores it. 16 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
