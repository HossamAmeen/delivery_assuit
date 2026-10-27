# TASK-096: Driver profile and navigation

- **Backlog item:** BL-036
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-056
- **Estimate:** S

## Description
Driver nav (Home, My Orders, Profile) and a profile that shows the account status and cannot change it.

## Technical Notes
- See the description.

## Acceptance Criteria
- [x] Profile reachable from the driver area
- [x] Change password and logout stay reachable
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built the driver navigation (Assigned orders, My orders, Profile) in DriverLayout. The existing profile screen already shows name, phone and account status and has no status or role input; change password and logout stay in the header menu. en and ar. 3 tests; Vitest 418 passed, eslint clean, vite build ok. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
