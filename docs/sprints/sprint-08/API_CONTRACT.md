# API Contract — Sprint 08 (Tracking, dashboard, edit)

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-026, BL-027, BL-038, BL-039, BL-040, BL-049, BL-050 | **Task:** TASK-113
- **Builds on:** Sprint 07. Order lists, details, the timeline (`history`), and cancel already exist; this sprint adds a summary and an edit.

## Endpoints
| Method and path | Who | Task |
|-----------------|-----|------|
| `GET /orders/summary/` | any role, scoped | 114 |
| `PATCH /orders/{id}/` | owning client, staff | 115 |

The trader and client lists and details use the existing `GET /orders/` and `GET /orders/{id}/` (visibility rules of Sprint 05, `?status=` filter, pagination, timeline on the detail). The assigned driver's **name** is in `driver`; no driver phone reaches traders or clients (BR-16).

## Summary (BL-040)
`GET /orders/summary/` counts the orders the caller may see (the same set as the list):
```json
{ "total": 12, "waiting_review": 1, "waiting_for_driver": 2, "in_progress": 3, "delivered": 5, "cancelled": 1 }
```
`waiting_review` = `created`, `waiting_for_driver` = `available`, `in_progress` = `assigned`, `picked_up`, `in_delivery`. For a trader `waiting_review` is always 0 (they never see unreviewed orders). The counts add up to `total` and match the list filters.

## Edit before assignment (BL-026, BR-13)
`PATCH /orders/{id}/` — all fields optional, only the ones sent change.
- **Shop order:** `description`, `pickup_location`, `items` (replaces all lines), `delivery` or `delivery_saved_address`. `shop` cannot change (400 on `shop`); `pickup`, `pickup_saved_address` are refused.
- **Direct delivery:** `description` (3 to 1000), `pickup` or `pickup_saved_address`, `delivery` or `delivery_saved_address`. `items`, `pickup_location`, `shop` are refused.
- Same validation, place copying, and price snapshot as creation (new lines take the item's current price).
- Allowed only while the order is `created` or `available`. The owning client after assignment: 403. Staff after assignment: 400 on `status`. Delivered or cancelled: 400. Trader or driver: 403. Another client's order: 404.
- **Re-review (the simpler option):** editing an `available` order moves it back to `created` (history row with the editor as actor and reason "edited"), so staff review it again. A `created` order stays `created`. The driver is never involved (none is assigned yet).
- Response `{ "order": {...} }` (list-style object, no timeline).

## Change Log
| Date | Task | Change |
|------|------|--------|
| 2026-10-27 | TASK-113 | Contract created. |
