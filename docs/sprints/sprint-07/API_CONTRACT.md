# API Contract — Sprint 07 (Pricing, operations, management)

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-025, BL-027 (backend), BL-043, BL-054, BL-055, BL-056, BL-057, BL-058, BL-077 | **Task:** TASK-098
- **Status:** DRAFT for implementation. Changes go through the Team Leader and the Change Log.
- **Builds on:** Sprint 06. Staff means Admin and Manager (BR-14 does not matter here: no Admin accounts are managed by these endpoints).

## Endpoints
| Method and path | Who | Task |
|-----------------|-----|------|
| `PATCH /staff/items/{id}/` body `{ "price": 12.5 \| null }` | staff | 099 |
| `PATCH /orders/{id}/fee/` body `{ "delivery_fee": 25 }` | staff | 100 |
| `GET /orders/?created_from=&created_to=&search=` | any role, scoped | 101 |
| `POST /orders/{id}/cancel/` body `{ "reason": "..." }` | client owner, staff | 102 |
| `GET /staff/drivers/`, `GET /staff/drivers/{id}/` | staff | 104 |
| `GET /staff/traders/`, `GET /staff/traders/{id}/` | staff | 105 |
| `GET /staff/clients/`, `GET /staff/clients/{id}/` | staff | 106 |

Approve, activate, and deactivate stay on the Sprint 03 `/users/{id}/...` endpoints.

## Prices and fees (BR-17)
- Item price: staff only; 0 to 100000, 2 decimals, or `null` to clear. Records `price_set_by` and `price_set_at`. Response `{ "item": { id, name, description, is_hidden, price, shop: { id, name } } }`. Trader/client/driver: 403.
- A client's shop details already show `price` (Sprint 05).
- **Price snapshot:** when an order is created, each line stores the item's price at that moment (`unit_price`, may be `null`). Later price changes never change old orders.
- Order object: lines become `{ "name", "quantity", "price" }` (`price` = unit price or `null`), plus `items_total` = sum of `price × quantity` over priced lines, `null` when no line has a price.
- Delivery fee: staff may set or change it any time **until** `delivered` or `cancelled` (else 400 on `status`); value 0 to 100000, 2 decimals. Every change (also the one made by approve) writes a row (old, new, actor, time). Response `{ "order": {...} }`.

## Orders table and timeline
- New filters on `GET /orders/`: `created_from` and `created_to` (dates `YYYY-MM-DD`, inclusive), `search` (reference contains, case-insensitive). Bad date is 400. They only narrow what the caller may already see.
- `GET /orders/{id}/` adds `history`: `[ { "from_status", "to_status", "actor_name", "reason", "created_at" } ]`, oldest first. Shown to staff, the owning client, the assigned driver, and the shop's trader (whoever can see the order). The list does not include it.

## Cancel (BR-12)
- Client owner: while `created` or `available`; `reason` optional. After assignment: 403.
- Staff: any order not `delivered` or `cancelled`, `reason` required (3 to 500).
- A delivered or cancelled order: 400 on `status`. Cancelling an assigned order frees the driver (BR-1 counts only active statuses). Response `{ "order": {...} }`.

## Management lists
Common: `?search=` (name, and phone for digit-like text), `?status=` (`pending_approval`, `active`, `deactivated`, `rejected`), paginated, newest first. Deleted users never appear.
- Driver row: `{ id, full_name, phone, status, delivered_orders }`.
- Trader row: `{ id, full_name, phone, status, shop_name, shop_phone, orders }`.
- Client row: `{ id, full_name, phone, status, orders }`.
Detail: `{ "user": <Managed user of Sprint 03>, "orders_total", "recent_orders": [<order>, up to 20, newest first], ... }` plus
- driver: `delivered_orders`, `cancelled_orders`, `active_order_reference`;
- trader: `shop` (Sprint 04 shop object or `null`), `locations`, `items` (with price);
- client: nothing extra.

## Trader status effects (BL-043)
A trader who is `pending_approval`, `rejected`, or `deactivated` cannot call trader endpoints (the existing 403 codes apply), does not appear to clients, and the shop cannot be ordered from. Their old orders stay visible to staff.

## Change Log
| Date | Task | Change |
|------|------|--------|
| 2026-10-27 | TASK-098 | Contract created. |
