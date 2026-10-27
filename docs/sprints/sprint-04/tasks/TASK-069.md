# TASK-069: Client saved addresses

- **Backlog item:** BL-019, BL-076
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-066
- **Estimate:** S

## Description
`SavedAddress` (owner FK, name, address, coordinates) reusing the `PlaceFields` pieces from TASK-066. CRUD under `/api/v1/addresses/` for clients only. Limit 20.

## Technical Notes
- Same validation as locations, no pickup/delivery flags
- Soft delete

## Acceptance Criteria
- [x] Client manages only own addresses; others 404
- [x] Other roles 403
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Saved addresses live in apps/locations next to Location (shared PlaceFields). /api/v1/addresses/ CRUD for clients, limit 20, 404 for another client's row. 15 tests. Full backend suite 644 passed, 1 skipped; ruff and makemigrations --check clean. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
