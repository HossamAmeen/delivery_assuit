# TASK-134: Audit trail

- **Backlog item:** BL-069
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-132
- **Estimate:** L

## Description
New app with an append-only log, hooks, and a staff-only read endpoint.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Entries for every listed action
- [x] Entries cannot be edited or deleted
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built apps/audit (append-only AuditEntry: save/delete/update refuse in code, not in Django admin; migration 0001), services.log (never raises), hooks for order status and creation, fee, rating, item price and account approve/reject/activate/deactivate, and GET /staff/audit/ (staff only, read only, filters action, actor, target; no write endpoints). 13 tests; backend suite green. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
