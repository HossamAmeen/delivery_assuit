# API Contract — Sprint 09 (Ratings, performance, dashboard)

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-028, BL-051, BL-053, BL-060, BL-061, BL-062, BL-063 | **Task:** TASK-122
- **Builds on:** Sprint 08. BL-028 filters (`status`, `search` by reference, dates) were built in Sprint 07; this sprint only adds them to the client and trader screens.

## Endpoints
| Method and path | Who | Task |
|-----------------|-----|------|
| `POST /orders/{id}/rating/` body `{ "score": 5, "comment": "" }` | owning client | 123 |
| `GET /drivers/me/performance/?month=YYYY-MM` | driver | 124 |
| `GET /staff/drivers/performance/?month=&ordering=` | staff | 124 |
| `GET /staff/dashboard/?period=&from=&to=` | staff | 125 |

## Rating (BL-061, BL-051)
- Only the order's client, only on a `delivered` order, once. Score 1 to 5 (integer), comment optional, up to 500 characters (trimmed).
- Another client's order: 404. Not delivered: 400 on `status`. Already rated: 400 on `status` ("already rated"). Driver, trader, staff: 403.
- The rating is tied to the order and to the driver who delivered it.
- The order object gets `rating`: `{ "score", "comment", "created_at" }` or `null`. It is returned **only to the owning client** (and staff); never to the driver or trader (the driver sees aggregates only).
- Response 201 `{ "order": {...} }`.

## Performance (BL-062, BL-063, BL-060)
Metrics, for one driver and an optional calendar month (server time zone):
- `delivered`: orders delivered by the driver, counted in the month of delivery.
- `cancelled`: orders that were assigned to the driver and later cancelled, counted in the month of cancellation. Orders cancelled before assignment are never counted.
- `average_rating` (1 decimal, or `null` when there is none) and `rating_count`: ratings of orders delivered in the month.
- Without `month`, everything (all-time). A bad month is 400.

Driver (`GET /drivers/me/performance/`):
```json
{ "month": "2026-10", "delivered": 4, "cancelled": 1, "average_rating": 4.5, "rating_count": 2,
  "months": [ { "month": "2026-10", "delivered": 4, "cancelled": 1, "average_rating": 4.5, "rating_count": 2 } ] }
```
`months` lists every month with any activity, newest first, for the month picker. The driver sees only their own aggregates, never single ratings or comments. A new driver gets zeros, `average_rating: null`, `months: []`.

Staff overview (`GET /staff/drivers/performance/`): paginated rows `{ id, full_name, status, delivered, cancelled, average_rating, rating_count }` for every non-deleted driver, with `month` as above. `ordering=delivered` (default) or `ordering=rating`, both descending (drivers without ratings last for `rating`; ties by name). Other values are 400.

## Dashboard (BL-053)
`GET /staff/dashboard/` — staff only.
- Period filters the **orders** by creation time: `period=today|week|month|custom` (`week` = last 7 days including today, `month` = this calendar month), `custom` needs `from` and `to` (dates, inclusive; `from` after `to` or missing is 400). No `period` = all-time.
- Account counts are not filtered.
```json
{ "period": "all",
  "drivers": { "total": 9, "active": 5, "inactive": 2, "pending": 1, "rejected": 1 },
  "traders": { "total": 4, "active": 3, "inactive": 0, "pending": 1, "rejected": 0 },
  "clients": { "total": 20 },
  "orders": { "total": 30, "pending": 6, "in_progress": 8, "delivered": 14, "cancelled": 2 } }
```
`inactive` = `deactivated`, `pending` = `pending_approval`. For orders, `pending` = created + available, `in_progress` = assigned + picked up + in delivery. Deleted accounts are not counted.

## Change Log
| Date | Task | Change |
|------|------|--------|
| 2026-10-27 | TASK-122 | Contract created. |
