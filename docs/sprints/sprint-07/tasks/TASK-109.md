# TASK-109: Staff management lists

- **Backlog item:** BL-056, BL-057, BL-058
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-104, TASK-105, TASK-106
- **Estimate:** M

## Description
Routes `/admin/drivers`, `/admin/traders`, `/admin/clients` from one list view.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Search, status filter, paging, counts
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /admin/drivers, /admin/traders, /admin/clients from one StaffListView (kind prop): name (link to details), phone, shop name for traders, status, delivered orders or orders count; search and status filter after a short pause, paging, empty/error/offline retry; admin nav links. en and ar. 6 tests; Vitest 443 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
