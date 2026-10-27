# TASK-137: UX consistency and confirmations

- **Backlog item:** BL-068
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-136
- **Estimate:** M

## Description
One shared section navigation for all roles; confirmation before deactivating an account.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Same nav component for all areas
- [x] Deactivate asks first
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built one SectionNav used by the Admin, Trader, Client and Driver layouts (labelled landmark, touch-size links, same active style) and a confirmation before deactivating an account (users list and staff details; cancel order and delete user already asked). 13 new tests; existing specs updated; Vitest 581 passed. Primary actions sit in the existing fixed bottom navigation and full-width buttons; no further layout changes were needed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
