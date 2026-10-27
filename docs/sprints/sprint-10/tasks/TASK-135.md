# TASK-135: Notifications bell and list

- **Backlog item:** BL-066
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-133
- **Estimate:** L

## Description
Header bell with the unread count and a `/notifications` page with mark as read.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Message by kind, in en and ar
- [x] Links to the order
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built the header bell (NotificationBell: unread count, 99+ cap, refreshed every 30 s and when the tab returns, silent on errors) and /notifications (NotificationsView: sentence from the kind in en and ar, newest first, unread marked, open marks read, mark all read, unread-only filter, paging, links by role, empty/error/offline retry); src/api/notifications.js; test setup mocks the count so other specs stay hermetic. 14 tests; Vitest 561 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
