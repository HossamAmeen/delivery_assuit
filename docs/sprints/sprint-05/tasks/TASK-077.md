# TASK-077: Order models, reference, and lifecycle service

- **Backlog item:** BL-021, BL-022
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-076, TASK-066, TASK-068
- **Estimate:** L

## Description
New app `apps/orders`: `Order` (reference, client, shop, driver, pickup and delivery place snapshots, description, delivery_fee, status, cancel fields), `OrderItem` (name snapshot, quantity, optional link to ShopItem), `OrderStatusChange` (history). `services.transition(order, to, actor, reason)` enforcing the table in the contract.

## Technical Notes
- Reference `ORD-` plus padded id, set in the same transaction as the create
- Place data copied, never a foreign key to Location or SavedAddress
- Transition rules live only in the service; views call it
- Tests for every valid and every invalid (from, to, role) combination

## Acceptance Criteria
- [x] Order, items, and history persist with required fields
- [x] Every valid transition works for the right role only; all others are refused with a clear message
- [x] Terminal states cannot change
- [x] History row written on every change
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built app apps/orders: Order (place snapshots, ORD-000012 reference set after the first insert, nullable fee, cancel fields), OrderItem, OrderStatusChange, migration 0001, and lifecycle.transition (the only status writer: row lock, transition table by role, final states, active-driver check for assignment, history row on every change). 60 tests including the full 7x7 status matrix against 7 kinds of caller. Arabic messages added. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
