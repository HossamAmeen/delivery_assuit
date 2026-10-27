# TASK-093: Driver home: active order

- **Backlog item:** BL-029, BL-033
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-091
- **Estimate:** M

## Description
The driver home shows the active order prominently with the next action, or a friendly empty state.

## Technical Notes
- See the description.

## Acceptance Criteria
- [x] Shows reference, pickup, delivery, status, assigned time
- [x] Empty state when nothing is assigned
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built DriverHomeView as the /driver home (kept title, name and role): active orders from ?scope=active as prominent cards (reference, status, pickup, delivery, details, assigned time) with the one next-action button (new NextActionButton: disabled while saving, no double tap, reload on 400) and a details link; refresh button; friendly empty state; error/offline retry. New utils/format.formatDateTime; orders status and action labels in en and ar. 12 new tests; role-home spec mocks the orders API. Vitest 399 passed. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
