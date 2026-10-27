# TASK-123: Ratings: model, rules and endpoint

- **Backlog item:** BL-061, BL-051
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-122
- **Estimate:** M

## Description
`POST /orders/{id}/rating/`, `rating` on the order for the owner and staff.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Rules tested for every role and status
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built OrderRating (one per order, 1 to 5 check constraint, migration 0003) and POST /orders/{id}/rating/: only the owning client, only on a delivered order, once; comment optional up to 500; the order object carries rating for the owner and staff only (driver and trader never). 20 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
