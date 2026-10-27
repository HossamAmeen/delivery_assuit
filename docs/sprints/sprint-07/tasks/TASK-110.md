# TASK-110: Staff management details

- **Backlog item:** BL-056, BL-057, BL-058, BL-077
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-109, TASK-099
- **Estimate:** L

## Description
Detail screens with profile, approve/activate/deactivate, recent orders, trader items with price editor.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Actions work
- [x] Price editor works
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /admin/{drivers,traders,clients}/:id (StaffDetailView): profile, status, orders total, driver delivered/cancelled/active order, trader shop, locations and items, recent orders linking to the staff order screen; approve (pending driver or trader), activate, deactivate through the Sprint 03 endpoints; item price editor for traders (set, change, clear; validated 0 to 100000, 2 decimals; server errors on the field). en and ar. 14 tests; Vitest 459 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
