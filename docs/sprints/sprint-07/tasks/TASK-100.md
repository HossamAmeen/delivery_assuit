# TASK-100: Delivery fee changes with history

- **Backlog item:** BL-077
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-098
- **Estimate:** M

## Description
`PATCH /orders/{id}/fee/` and a fee-change record; approve writes one too.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Allowed until delivered or cancelled
- [x] Each change records old, new, who, when
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built PATCH /orders/{id}/fee/ (staff, until delivered or cancelled) with OrderFeeChange rows (old, new, actor, time); approve writes one too. Tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
