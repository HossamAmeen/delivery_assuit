# TASK-068: Shop items (flat list, hide, no price)

- **Backlog item:** BL-042
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-067
- **Estimate:** M

## Description
`ShopItem` (shop FK, name, description, is_hidden, price nullable and not writable) with CRUD under `/api/v1/shop/items/`. Filters `hidden` and `search`.

## Technical Notes
- Name unique per shop among live items, case-insensitive (constraint plus a friendly 400)
- Price ignored on write, `null` on read
- Soft delete; limit 200 live items

## Acceptance Criteria
- [x] Trader sees and changes only own items; another shop's item is 404
- [x] Hidden items stay in the trader's list and can be unhidden
- [x] Duplicate name is 400 on `name`
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built ShopItem (flat, hide flag, read-only null price, case-insensitive unique name per shop via constraint plus friendly 400, limit 200, soft delete) with /api/v1/shop/items/ CRUD, filters hidden and search. 25 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
