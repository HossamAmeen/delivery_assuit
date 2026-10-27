# TASK-129: Admin dashboard cards with a time filter

- **Backlog item:** BL-053
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-125
- **Estimate:** M

## Description
Cards on the admin home.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built AdminHomeView as the /admin home (keeps title, name, role): drivers, traders (total, active, inactive, pending) and clients cards, order counts (total, pending, in progress, delivered, cancelled) with a period filter (all time default, today, last 7 days, this month, custom range that waits for a valid range), help text for the groupings, empty state, error retry. en and ar. 8 tests; Vitest 544 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
