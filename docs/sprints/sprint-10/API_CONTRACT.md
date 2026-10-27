# API Contract — Sprint 10 (Notifications, audit trail)

- **Owner:** backend | **Consumers:** frontend, QA | **Backlog:** BL-066, BL-067 (frontend), BL-068 (frontend), BL-069 | **Task:** TASK-132
- **Builds on:** Sprint 09. In-app only: no push, SMS, or email (BL-066).

## Endpoints
| Method and path | Who | Task |
|-----------------|-----|------|
| `GET /notifications/?unread=true` | any operational user, own only | 133 |
| `GET /notifications/unread-count/` | any operational user | 133 |
| `POST /notifications/{id}/read/` | owner | 133 |
| `POST /notifications/read-all/` | any operational user | 133 |
| `GET /staff/audit/?action=&actor=` | staff | 134 |

## Notifications (BL-066)
Object: `{ "id", "kind", "order_id", "reference", "read", "created_at" }` where `order_id` and `reference` are `null` for account notifications. The frontend builds the sentence from `kind`, so it follows the UI language.

| `kind` | Recipients | When |
|--------|-----------|------|
| `order_waiting_review` | every Admin and Manager | a client creates an order, or edits an approved one back to review |
| `account_waiting_approval` | every Admin and Manager | a driver or trader registers |
| `order_approved` | the client | review approves the order |
| `order_rejected` | the client | review rejects the order |
| `order_assigned` | the driver and the client | assignment |
| `order_picked_up`, `order_in_delivery`, `order_delivered` | the client | the driver advances the order |
| `order_cancelled` | the client; the assigned driver (if any) | cancel or reject. The person who cancelled is not notified about their own action. |

- Users see only their own notifications. Someone else's id is 404. Newest first, paginated; `unread=true` filters.
- `unread-count`: `{ "count": 3 }`. `read`: marks one (idempotent) and returns it. `read-all`: marks all of the caller's, returns `{ "marked": n }`.
- A deactivated account gets 403 as everywhere else.
- Notifications are written in the same transaction as the change; a failure to notify never blocks the action's own result (the notification step cannot raise).

## Audit trail (BL-069)
Entry: `{ "id", "action", "actor": { "id", "full_name" } | null, "target_type", "target_id", "detail", "created_at" }`, newest first, paginated, read only. `detail` is a short text (for example `available -> assigned`, `fee 20.00 -> 25.00`).
- Recorded: `order.status` (every status change and creation), `order.fee`, `order.rating`, `item.price`, `account.approved`, `account.rejected`, `account.activated`, `account.deactivated`.
- Only Admin and Manager can read it. There is no create, edit, or delete endpoint, and the model refuses updates and deletes in code.
- Filters: `action` (exact), `actor` (user id), `target_type` + `target_id`. Unknown `action` values return an empty list.

## Change Log
| Date | Task | Change |
|------|------|--------|
| 2026-10-27 | TASK-132 | Contract created. |
