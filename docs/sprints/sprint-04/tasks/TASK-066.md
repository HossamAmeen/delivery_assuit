# TASK-066: Trader locations (CRUD, pickup/delivery flags, default pickup)

- **Backlog item:** BL-017, BL-018, BL-020
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-065
- **Estimate:** M

## Description
New app `apps/locations`. `Location` model (owner FK to User, name, address, latitude, longitude, is_pickup, is_delivery, is_default_pickup) on `BaseModel` (soft delete). CRUD under `/api/v1/locations/` for traders only.

## Technical Notes
- Own rows only; another trader's id is 404
- Coordinates validated together and in range; name and address trimmed and length checked
- `is_pickup` or `is_delivery` must be true
- One default pickup per trader, kept consistent on create, patch, and delete, in a transaction
- Soft delete; limit of 50 live locations
- Abstract `PlaceFields` model/serializer mixin reused by TASK-069

## Acceptance Criteria
- [x] Trader can create, list, edit, and delete only their own locations
- [x] Invalid coordinates and missing name or address are 400 with field errors
- [x] Default pickup moves as described in the contract
- [x] Client, driver, admin get 403; anonymous 401
- [x] Tests written and passing; ruff and `makemigrations --check` clean

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built new app apps/locations: Location and SavedAddress models (PlaceFields base, soft delete), migration 0001, services (limit 50, one default pickup kept in a transaction, promotion on delete or pickup off), LocationSerializer, /api/v1/locations/ CRUD for traders. Other traders' rows are 404. Arabic strings added. 40 tests; full suite 575 passed, 1 skipped; ruff and makemigrations --check clean. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
