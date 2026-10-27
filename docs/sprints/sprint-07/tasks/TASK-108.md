# TASK-108: Staff order details: timeline, fee, cancel, actions

- **Backlog item:** BL-054, BL-055, BL-077
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-100, TASK-101, TASK-102
- **Estimate:** L

## Description
Route `/admin/orders/:id` with timeline, fee editor, cancel with reason, links to review and assign.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Actions per status
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /admin/orders/:id (StaffOrderView): details with client and shop phones, items with prices and total, fee, status timeline with actor and reason; fee editor (validated, until finished), cancel with a required reason, links to review (created) and assignment (available); finished orders offer no controls; refused actions reload. en and ar. 11 tests; Vitest 437 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
