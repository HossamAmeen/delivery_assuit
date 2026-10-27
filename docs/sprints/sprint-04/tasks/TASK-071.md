# TASK-071: Trader shop profile and items screens

- **Backlog item:** BL-041, BL-042
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-067, TASK-068
- **Estimate:** M

## Description
Trader routes `/trader/shop` (profile, availability switch, a clear note when `can_accept_orders` is false and why) and `/trader/shop/items` (list, add, edit, hide or show, delete).

## Technical Notes
- `src/api/shop.js`
- Items show no price field
- Trader nav gets Shop and Items links

## Acceptance Criteria
- [x] Profile edit and availability toggle work
- [x] Item add, edit, hide, delete work; duplicate name error on the field
- [x] Empty, loading, error states
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built routes /trader/shop (TraderShopView: edit name, phone, description, availability switch, clear reason when can_accept_orders is false) and /trader/shop/items (TraderItemsView: add, edit, hide or show, delete with confirmation, no price field), src/api/shop.js, trader nav links, en and ar. 16 new tests; Vitest 310 passed, eslint clean. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
