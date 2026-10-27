# TASK-133: In-app notifications

- **Backlog item:** BL-066
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-132
- **Estimate:** L

## Description
New app with the model, hooks in the lifecycle and registration, and the four endpoints.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Each recipient rule tested
- [x] Users see only their own
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built apps/notifications (Notification model, migration 0001; services hooked into lifecycle.transition, order creation and registration; list with ?unread=, unread-count, mark read, read-all). Recipient rules per the contract (staff for new or re-reviewed orders and driver/trader registrations; client for approved, rejected, assigned, picked up, in delivery, delivered, cancelled; driver for assigned and cancelled; the actor is never told about their own action; inactive staff skipped). Notification failures never block the action. 22 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
