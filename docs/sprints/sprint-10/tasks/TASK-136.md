# TASK-136: Auto-refresh of order screens

- **Backlog item:** BL-067
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-135
- **Estimate:** M

## Description
A composable that refreshes quietly on an interval and when the tab returns; applied to the driver home, order lists and details, review and assign queues.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Does not interrupt input or lose the place
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built useAutoRefresh (interval and on tab return; skips hidden tabs and offline; never overlaps; swallows errors) and a quiet load({silent}) on the driver home, order lists, client and trader order details, review and assign queues: no spinner, errors ignored, typed reasons, chosen drivers and open panels are kept. 12 tests; Vitest 571 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
