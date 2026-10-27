# TASK-070: Trader locations screens

- **Backlog item:** BL-017, BL-018, BL-020
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-066
- **Estimate:** M

## Description
Trader area route `/trader/locations`: list with pickup/delivery/default badges, add and edit form (name, address, optional coordinates, two checkboxes, default option), delete with confirmation.

## Technical Notes
- Use `FormField`, `ListStatus`, `serverFieldErrors`; add `src/api/locations.js`
- Coordinates: two optional number inputs, both or neither
- Strings in en and ar with identical keys
- Trader nav gets a Locations link

## Acceptance Criteria
- [x] List, add, edit, delete work against the contract (mocked in Vitest)
- [x] Server field errors show on the matching field
- [x] Empty, loading, error states
- [x] Tests written and passing; eslint clean

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built route /trader/locations (TraderLocationsView), trader nav, src/api/locations.js, shared PlaceFields component and utils/places.js (reused by TASK-073). List with pickup/delivery/default badges, add and edit form with optional coordinate pair, delete with confirmation, loading/empty/error/offline states, server field errors, en and ar. 17 new tests; Vitest 294 passed, eslint clean. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
