# TASK-067: Shop profile and availability

- **Backlog item:** BL-041
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-065
- **Estimate:** S

## Description
New app `apps/shops`. `Shop` (OneToOne trader, name, phone, description, is_available) with `GET`/`PATCH /api/v1/shop/`. Created lazily on first read. Add `shops.services.is_shop_orderable` and `pickup_locations` (reads `Location`).

## Technical Notes
- Phone uses `apps.users.phone` normalisation
- `can_accept_orders` is computed, read-only
- Unavailable shops and shops without a pickup location are not orderable (helper, unit tested)

## Acceptance Criteria
- [x] Trader reads and edits own shop; other roles 403
- [x] Availability toggle works and `can_accept_orders` reflects pickup locations and account status
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built app apps/shops: Shop model (OneToOne trader, lazy create, unavailable by default), GET/PATCH /api/v1/shop/, phone normalised and optional, can_accept_orders computed, helpers is_shop_orderable and pickup_locations. 26 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
