# TASK-120: Client edit order

- **Backlog item:** BL-026
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-115, TASK-119
- **Estimate:** L

## Description
Route `/client/orders/:id/edit`, only while created or available.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Edit shows a re-review notice for available orders
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /client/orders/:id/edit (ClientEditOrderView): current values filled in; shop orders can change items (quantities prefilled by name), pickup place, delivery place, note; direct orders change both places and the details (still mandatory); re-review notice for approved orders; closed shop still allows editing the delivery; locked message from assignment on; a refusal at save time reloads and locks. orders API updateOrder. en and ar. 18 tests; Vitest 512 passed. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
