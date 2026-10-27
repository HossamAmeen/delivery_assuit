# TASK-081: Order review: approve and reject

- **Backlog item:** BL-023
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-077, TASK-078
- **Estimate:** M

## Description
`POST /orders/{id}/approve/` (optional delivery fee) and `/reject/` (reason), Admin and Manager only, through `transition`.

## Technical Notes
- Fee is stored on approve; BR-17 means nobody else can set it

## Acceptance Criteria
- [x] Approve makes the order available and records who and when
- [x] Reject cancels with the reason visible to the client
- [x] Repeats and other roles are refused
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built POST /orders/{id}/approve/ (optional delivery_fee 0 to 100000, 2 decimals) and /reject/ (reason 3 to 500) for Admin and Manager, through lifecycle.transition via orders/review.py. A test found that reject would have cancelled an already available order; review now accepts created orders only (400 on status otherwise). Repeats are 400 with one history row; fee is stored only if the move succeeds. Arabic messages added. 48 new tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
