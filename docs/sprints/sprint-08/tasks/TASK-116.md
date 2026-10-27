# TASK-116: Trader orders list and details

- **Backlog item:** BL-038, BL-039, BL-027
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-101
- **Estimate:** M

## Description
Routes `/trader/orders` and `/trader/orders/:id` (read only) with driver name or waiting message and the timeline.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] No create, edit, cancel controls
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /trader/orders (shared OrderListView with base='trader': status filter without the unreviewed status, paging, reference link, places, date) and /trader/orders/:id (TraderOrderView, read only: OrderDetails with driver name or 'waiting for a driver', items, fee, cancel reason, OrderTimeline; refresh button; no create, edit or cancel controls; no phone). New shared components OrderDetails and OrderTimeline. en and ar. 10 tests; Vitest 473 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
