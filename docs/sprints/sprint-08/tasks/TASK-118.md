# TASK-118: Client orders list

- **Backlog item:** BL-049
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-101
- **Estimate:** M

## Description
Route `/client/orders` with status filter, active orders highlighted, paging; home link enabled.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /client/orders (shared OrderListView with base='client': all statuses, active orders highlighted, status filter, paging) with a client nav link; the client home 'My orders' is a link now. 3 tests incl. updated client-home spec. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
