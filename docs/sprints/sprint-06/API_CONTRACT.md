# API Contract — Sprint 06 (Assignment and driver execution)

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-029, BL-030, BL-031, BL-032, BL-033, BL-034, BL-036 | **Task:** TASK-088
- **Status:** DRAFT for implementation. Any change goes through the Team Leader and is recorded in the Change Log.
- **Builds on:** `../sprint-05/API_CONTRACT.md`. Envelope, pagination, errors, the order object, visibility, and the lifecycle table still apply. Drivers have no accept, un-accept, or release action (BR-4).

## Endpoints
| Method and path | Who | Task | Purpose |
|-----------------|-----|------|---------|
| `GET /drivers/` | admin, manager | 089 | Active drivers with their busy state. `?available=true` hides busy ones. |
| `POST /orders/{id}/assign/` | admin, manager | 089 | `available` to `assigned`. Body `{ "driver": 5 }`. |
| `POST /orders/{id}/advance/` | the assigned driver | 090 | The next execution step. No body. |
| `GET /orders/?scope=active\|history` | any role, scoped | 091 | Active or finished orders. |

Anonymous is 401, a role that may not use an endpoint is 403, an order the caller cannot see is 404.

## Drivers (`GET /drivers/`)
Row: `{ "id", "full_name", "phone", "has_active_order", "active_order_reference" }`. Only `active` drivers appear. Pending, rejected, deactivated, and deleted drivers never do. `active_order_reference` is `null` when free. Paginated, ordered by name.

## Assign (BL-031)
- Body: `{ "driver": <user id> }`, required.
- The order must be `available`, else 400 on `status` (this covers `cancelled` (BR-3) and an order someone else just assigned).
- The driver must be an `active` driver, else 400 on `driver` ("Choose an active driver.").
- BR-1: a driver who has an order in `assigned`, `picked_up`, or `in_delivery` is refused, 400 on `driver` ("This driver already has an active order.").
- Two staff assigning the same order, or two orders to the same driver, at once: exactly one succeeds; the other gets the 400 above.
- Response `{ "order": {...} }`; the history row records the actor and time. `assigned_at` is set.

## Advance (BL-032)
The server picks the step, so a client cannot skip one:

| Order status | Becomes | `next_action` |
|--------------|---------|---------------|
| `assigned` | `picked_up` | `pick_up` |
| `picked_up` | `in_delivery` | `start_delivery` |
| `in_delivery` | `delivered` | `deliver` |

Any other status is 400 on `status`. A driver other than the assigned one gets 404. Admin, Manager, client, and trader get 403. A repeated call moves one more step, never twice for one tap: the response carries the new `next_action`, and the frontend disables the button while the request runs.

## Order object additions
| Field | Meaning |
|-------|---------|
| `assigned_at` | ISO time of the assignment, or `null` |
| `delivered_at` | ISO time of delivery, or `null` |
| `next_action` | `pick_up`, `start_delivery`, `deliver`, or `null`. Non-null **only** for the assigned driver, while the order is active. |

Contact numbers (BR-16):
- `client.phone` and `shop.phone` (the shop's contact number, may be `""`) are returned to Admin and Manager always.
- They are returned to the **assigned driver only while the order is `assigned`, `picked_up`, or `in_delivery`**. After `delivered` or `cancelled` they are removed again.
- Never to a client (for the shop), a trader (for the client), or an unassigned driver.
- `shop` becomes `{ "id", "name" }` plus `phone` when allowed. The driver's own phone is still never sent to clients or traders.

## Lists (BL-029, BL-034)
- `?scope=active`: status in `assigned`, `picked_up`, `in_delivery`, newest assignment first.
- `?scope=history`: status in `delivered`, `cancelled`, newest first.
- Combines with `?status=`. Other scope values are 400. Visibility is unchanged: a driver sees only their own orders; an order cancelled by staff leaves the driver's active list and appears in history; a driver with a cancelled order is free for a new assignment.

## Change Log
| Date | Task | Change |
|------|------|--------|
| 2026-10-27 | TASK-088 | Contract created. |
| 2026-10-27 | TASK-089..091 | Built as written. The existing Sprint 05 rule that a driver gets no phone was replaced by the BR-16 rule above. |
