# TASK-125: Staff dashboard counts with a period filter

- **Backlog item:** BL-053
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-122
- **Estimate:** M

## Description
`GET /staff/dashboard/`.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Counts match known data
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built GET /staff/dashboard/?period=today|week|month|custom&from=&to= (orders filtered by creation date, accounts not filtered): drivers and traders by active, inactive (deactivated), pending, rejected; clients total; orders total, pending (created+available), in progress, delivered, cancelled. Bad periods are 400. 15 tests; backend suite green. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
