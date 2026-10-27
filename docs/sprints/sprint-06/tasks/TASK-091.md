# TASK-091: Driver lists, details, and contact numbers

- **Backlog item:** BL-029, BL-030, BL-034
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-090
- **Estimate:** M

## Description
Add `scope=active|history`, `assigned_at`, `delivered_at`, `next_action`, and the BR-16 phone rules to the order object.

## Technical Notes
- assigned_at and delivered_at come from the history rows

## Acceptance Criteria
- [x] Active and history lists behave as in the contract
- [x] Phones appear only for the assigned driver while the order is active, and for staff
- [x] A cancelled order leaves the active list and frees the driver
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Order list gets ?scope=active|history (active: newest assignment first), the order object gets assigned_at, delivered_at (from the history rows) and next_action (assigned driver only). BR-16: client and shop phones go to staff always and to the assigned driver only while the order is assigned, picked up, or in delivery; never to clients (shop or driver phone) or traders (client phone). Existing visibility test updated for the new driver rule. 17 new tests; full suite green. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
