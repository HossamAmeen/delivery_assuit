# API Contract — Sprint 05 (Orders and review)

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-021, BL-022, BL-023, BL-024, BL-045, BL-046, BL-047, BL-048 | **Task:** TASK-076
- **Status:** DRAFT for implementation. Any change goes through the Team Leader and is recorded in the Change Log.
- **Builds on:** `../sprint-04/API_CONTRACT.md` and the Sprint 03 base. Envelope, pagination, error bodies, ownership rule (someone else's row is **404**) still apply.

## Endpoints
| Method and path | Who | Task | Purpose |
|-----------------|-----|------|---------|
| `GET /shops/` | client | 079 | Shops clients can order from. `?search=` on name. Paginated. |
| `GET /shops/{id}/` | client | 079 | One shop with visible items and pickup locations. |
| `POST /orders/` | client | 080 | Create a shop order or a direct delivery. |
| `GET /orders/` | any role, scoped | 078 | Orders the caller may see. `?status=`. Paginated, newest first. |
| `GET /orders/{id}/` | any role, scoped | 078 | One order, or 404. |
| `POST /orders/{id}/approve/` | admin, manager | 081 | CREATED to AVAILABLE. Optional `delivery_fee`. |
| `POST /orders/{id}/reject/` | admin, manager | 081 | CREATED to CANCELLED with a required reason. |

Anonymous is 401. A role that may not use an endpoint gets 403. All use the `user` throttle scope.

## Shops for clients
Row: `{ "id", "name", "description" }`. No phone (BR-16 keeps contact numbers private).

Detail:
```json
{ "id": 1, "name": "Ahmed Store", "description": "",
  "items": [ { "id": 7, "name": "Cheese pie", "description": "", "price": null } ],
  "pickup_locations": [ { "id": 3, "name": "Main branch", "address": "12 Nile St", "is_default": true } ] }
```
- Only shops where `is_shop_orderable` is true are listed. Any other shop id, including a closed one, is **404**.
- `items` are the shop's live, non-hidden items. `price` is `null` until Sprint 07.
- `pickup_locations` come from `pickup_locations(shop)`, default first.

## Create an order (`POST /orders/`)
**Shop order** (body has `shop`):
```json
{ "shop": 1, "pickup_location": 3,
  "items": [ { "item": 7, "quantity": 2 } ],
  "description": "No onions",
  "delivery": { "name": "Home", "address": "5 Garden St", "latitude": 30.05, "longitude": 31.23 } }
```
- `pickup_location` optional: default is the shop's default pickup. It must be one of the shop's pickup locations.
- `items` required, 1 to 50 lines, each `item` unique in the list, `quantity` 1 to 99. Items must belong to that shop and be live and not hidden.
- `description` optional, up to 1000.
- Delivery place: send `delivery` (place object, rules as in Sprint 04) **or** `delivery_saved_address` (id of the caller's saved address), not both, and one is required.

**Direct delivery** (no `shop`):
```json
{ "pickup": { "name": "Office", "address": "1 Tahrir Sq" },
  "delivery": { "name": "Mum", "address": "9 Rose St" },
  "description": "A box of documents" }
```
- `pickup` or `pickup_saved_address`, and `delivery` or `delivery_saved_address`: exactly one of each pair.
- `description` required, 3 to 1000 characters.
- `items`, `pickup_location` are not accepted (400).

Both: the place data is **copied into the order**, so later edits or deletes of a location or saved address never change an order. The status is `created`. `delivery_fee` is `null`. The caller must be an `active` client. Response 201 `{ "order": {...} }`.

Errors: 400 with field keys (`shop`, `items`, `items.0.item` as `items`, `delivery`, `pickup`, `description`, `non_field_errors`). A shop that is not orderable is 400 on `shop`. A foreign saved address is 400 on its field (never reveals it exists).

## Order object
```json
{ "id": 12, "reference": "ORD-000012", "status": "created",
  "client": { "id": 4, "full_name": "Mona", "phone": "0100..." },
  "shop": { "id": 1, "name": "Ahmed Store" },
  "driver": null,
  "pickup": { "name": "Main branch", "address": "12 Nile St", "latitude": null, "longitude": null },
  "delivery": { "name": "Home", "address": "5 Garden St", "latitude": 30.05, "longitude": 31.23 },
  "description": "No onions",
  "items": [ { "name": "Cheese pie", "quantity": 2 } ],
  "delivery_fee": null,
  "cancel_reason": "", "cancelled_at": null,
  "created_at": "2026-10-27T10:00:00Z", "modified_at": "2026-10-27T10:00:00Z" }
```
- `reference` is `ORD-` plus the id left-padded to 6 digits. Unique, never reused.
- `shop` and `driver` are `null` when absent. `driver` is `{ "id", "full_name" }` (no phone in this sprint; BR-16).
- `client.phone` is returned to **Admin and Manager only**. It is absent for every other role.
- `status` values: `created`, `available`, `assigned`, `picked_up`, `in_delivery`, `delivered`, `cancelled`.
- `delivery_fee` is a JSON number or `null`.
- `cancel_reason` is the Admin/Manager's reason on a rejection; `""` otherwise.

## Visibility (BL-024)
| Role | Sees |
|------|------|
| Client | Own orders (BR-6) |
| Trader | Orders to their shop that have been approved at least once (BR-7, BR-11). A rejected-while-created order is never shown to the trader. |
| Driver | Only orders assigned to them (BR-5) |
| Admin, Manager | All (BR-8) |

Anything else is 404, in the list (absent) and in the detail.

## Lifecycle (BL-022)
Valid moves, and who may make them:

| From | To | Who |
|------|----|-----|
| created | available | Admin, Manager (review) |
| created | cancelled | Admin, Manager (reject); the owning client (cancel) |
| available | assigned | Admin, Manager (assignment, Sprint 06) |
| available | cancelled | Admin, Manager; the owning client |
| assigned | picked_up | the assigned driver |
| assigned | cancelled | Admin, Manager only |
| picked_up | in_delivery | the assigned driver |
| picked_up, in_delivery | cancelled | Admin, Manager only |
| in_delivery | delivered | the assigned driver |

`delivered` and `cancelled` are final (BR-2, BR-3). Skipping a step, going backwards, or a move by the wrong role is refused in the service layer with a clear message. Every change writes a history row (order, from, to, actor, reason, time). This sprint only exposes review through the API; the other moves are service functions used by later sprints.

## Review
- `POST /orders/{id}/approve/` body `{ "delivery_fee": 25.5 }` (optional; 0 to 100000, 2 decimals). Only from `created`; else 400 on `status`.
- `POST /orders/{id}/reject/` body `{ "reason": "..." }` required, 3 to 500 characters. Only from `created`.
- Both return `{ "order": {...} }`. A repeated call is 400, not a second history row.

## Limits and codes
No new `code`. Order-state errors use 400 with the key `status`.

## Change Log
| Date | Task | Change |
|------|------|--------|
| 2026-10-27 | TASK-076 | Contract created. |
| 2026-10-27 | TASK-077..081 | Built as written. Review (approve and reject) refuses any order that is not `created`, including reject on an `available` order (a test found the lifecycle alone would allow that; it is a different action, BL-025). New message `Only a new order can be reviewed.` |
