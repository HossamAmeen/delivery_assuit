# TASK-072: Client home

- **Backlog item:** BL-044
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-055 (account screens exist)
- **Estimate:** S

## Description
Client home route shows two entries (Order from a shop, Deliver from place to place), quick links to My Orders and Profile. The order screens do not exist yet, so those entries are visible but marked as coming soon and not clickable.

## Technical Notes
- No fake orders; recent active order block is omitted until orders exist

## Acceptance Criteria
- [x] Client sees both entries and the Profile link
- [x] Entries for later sprints are clearly disabled with an accessible label
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built ClientHomeView as the /client home: two entries (Order from a shop, Deliver from place to place) shown disabled with a Coming soon note, Profile link, My orders marked coming soon, no invented orders. The recent-order block is omitted until orders exist. en and ar. 6 new tests; role-home spec updated for the client. Vitest 316 passed, eslint clean, vite build ok. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
