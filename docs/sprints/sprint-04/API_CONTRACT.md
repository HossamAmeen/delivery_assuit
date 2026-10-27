# API Contract — Sprint 04 (Locations, shop, saved addresses)

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-017, BL-018, BL-019, BL-020, BL-041, BL-042, BL-076 | **Task:** TASK-065
- **Status:** DRAFT for implementation. Any change goes through the Team Leader and is recorded in the Change Log.
- **Builds on:** `../sprint-03/API_CONTRACT.md`. The envelope (`{success, message, data}` / `{success:false, message, errors, code?}`), `/api/v1/` prefix, `Accept-Language`, pagination `data: {count, next, previous, results}`, and the standard 400/401/403/404/405/429/500 bodies still apply.

## Endpoints
| Method and path | Who | Purpose |
|-----------------|-----|---------|
| `GET /locations/` | trader | Own locations, newest first, paginated |
| `POST /locations/` | trader | Create a location |
| `GET/PATCH/DELETE /locations/{id}/` | trader (owner) | Read, edit, delete one |
| `GET /shop/` | trader | Own shop profile (created on first read) |
| `PATCH /shop/` | trader | Edit name, phone, description, availability |
| `GET /shop/items/` | trader | Own items, paginated |
| `POST /shop/items/` | trader | Add an item |
| `GET/PATCH/DELETE /shop/items/{id}/` | trader (owner) | Read, edit (incl. hide), delete |
| `GET /addresses/` | client | Own saved addresses, paginated |
| `POST /addresses/` | client | Save an address |
| `GET/PATCH/DELETE /addresses/{id}/` | client (owner) | Read, edit, delete |

Everyone else gets 401 (anonymous) or 403 (any other role). Another user's row is **404**, never 403, so ids do not leak. All endpoints use the `user` throttle scope. 

## Response bodies
Single-object calls return the object under one key in `data`: `{ "location": {...} }`, `{ "shop": {...} }`, `{ "item": {...} }`, `{ "address": {...} }`. Create is 201, edit is 200. Delete is 200 with `data: {}`. Lists return `data: {count, next, previous, results: [...]}` with the bare objects in `results`.

## Place fields (shared by locations and addresses)
| Field | Type | Rules |
|-------|------|-------|
| `name` | string | required, trimmed, 2 to 100 characters |
| `address` | string | required, trimmed, 3 to 500 characters |
| `latitude` | number or `null` | optional, -90 to 90, up to 6 decimals |
| `longitude` | number or `null` | optional, -180 to 180, up to 6 decimals |

Latitude and longitude come together: sending only one is a 400 on the missing one. Both `null` (or both omitted) is fine. They are returned as JSON numbers or `null`.

## Location (trader)
```json
{ "id": 3, "name": "Main branch", "address": "12 Nile St, Cairo",
  "latitude": 30.0444, "longitude": 31.2357,
  "is_pickup": true, "is_delivery": false, "is_default_pickup": true,
  "created_at": "2026-10-27T10:00:00Z" }
```
- `is_pickup` defaults **true**, `is_delivery` defaults **false** (BL-018). A location with both false is a 400 on `is_pickup` ("Choose pickup, delivery, or both.").
- `is_default_pickup` (BL-020): at most one per trader. Setting it to true clears it on the trader's other locations in the same transaction. It needs `is_pickup` true (400 on `is_default_pickup` otherwise). The trader's first pickup location becomes the default automatically.
- Turning `is_pickup` off on the default clears the default and promotes the oldest remaining pickup location, if any.
- Deleting is a soft delete. Deleting the default promotes the oldest remaining pickup location, if any. Future orders store their own copy of the place, so history is not affected.
- A trader may have up to 50 live locations; the 51st is a 400 on `non_field_errors`.

## Shop
```json
{ "id": 1, "name": "Ahmed Store", "phone": "01001234567", "description": "",
  "is_available": false, "can_accept_orders": false }
```
- Created on the first `GET /shop/` with `name` = the trader's `full_name`, `phone` = the trader's phone, `is_available` **false**.
- Editable: `name` (required, 2 to 100), `phone` (same rules and normalisation as account phone, optional here; `""` clears it), `description` (up to 500), `is_available` (boolean).
- `can_accept_orders` is read-only: shop available **and** at least one live pickup location **and** the trader's account `active`. Setting `is_available` to true with no pickup location is allowed; `can_accept_orders` stays false and the screen shows why.
- Only an approved (`active`) trader reaches these endpoints; a pending or rejected trader is 403 as for any other protected call.

## Shop item (trader)
```json
{ "id": 7, "name": "Cheese pie", "description": "", "is_hidden": false,
  "price": null, "created_at": "2026-10-27T10:00:00Z" }
```
- Writable: `name` (required, 2 to 100), `description` (up to 300), `is_hidden`. `price` is read-only, always `null` in this sprint (BR-17, set in Sprint 07). A `price` in the request body is ignored.
- Item names are unique per shop among live items, case-insensitive. Duplicate: 400 on `name`.
- Hiding does not delete. Delete is a soft delete. Up to 200 live items per shop.
- List filter: `?hidden=true|false`. Search: `?search=` (name contains).

## Saved address (client)
Same shape as the place fields plus `id` and `created_at`. Up to 20 per client; the 21st is a 400 on `non_field_errors`.

## Helpers for later sprints (no endpoint)
- `shops.services.is_shop_orderable(shop)`: the `can_accept_orders` rule.
- `shops.services.pickup_locations(shop)`: the trader's live pickup-enabled locations, default first.
- Order sprints must call these; they must never list a shop themselves.

## Error codes
No new `code`. Validation failures are 400 with field keys as above.

## Change Log
| Date | Task | Change |
|------|------|--------|
| 2026-10-27 | TASK-065 | Contract created. |
| 2026-10-27 | TASK-066..069 | Built as written. Added the response-body wrapper keys. Saved addresses live in the `locations` app; shop and items in the `shops` app. |
