# TASK-073: Client saved addresses screens

- **Backlog item:** BL-076, BL-019
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-069
- **Estimate:** M

## Description
Client route `/client/addresses`: list, add, edit, delete. A small reusable `PlaceForm` for name, address, optional coordinates, shared with the trader locations form.

## Technical Notes
- `src/api/addresses.js`
- Client home and nav link to Addresses

## Acceptance Criteria
- [x] CRUD works against the contract
- [x] Empty, loading, error states
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built route /client/addresses (ClientAddressesView): list, add, edit, delete with confirmation, reuses PlaceFields and utils/places, src/api/addresses.js, client nav and a home link, loading/empty/error/offline states, en and ar. 9 new tests; Vitest 325 passed, eslint clean. Not run in a browser. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
