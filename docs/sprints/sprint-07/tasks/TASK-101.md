# TASK-101: Orders table filters and status timeline

- **Backlog item:** BL-054, BL-027
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-098
- **Estimate:** M

## Description
`created_from`, `created_to`, `search` on the orders list; `history` on the detail.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Filters never widen visibility
- [x] History visible to everyone who can see the order
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Orders list gets created_from, created_to (inclusive dates) and search (reference contains); detail gets the status timeline (history oldest first with actor and reason) for anyone who can see the order; filters never widen visibility. Prefetch of history actors. 9 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
