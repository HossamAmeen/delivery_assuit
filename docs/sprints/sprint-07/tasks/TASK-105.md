# TASK-105: Staff traders list and detail

- **Backlog item:** BL-057
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-098
- **Estimate:** M

## Description
`/staff/traders/`.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Shop info, order count, detail with locations and items
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built under /staff/: drivers, traders and clients lists (rows with counts, search by name or digit-like phone, status filter, paging, deleted hidden) and details (managed user, orders_total, up to 20 recent orders, plus driver performance summary, or trader shop, locations and items with prices). Staff only. Tests in test_staff_management.py; backend suite 1035 passed, 1 skipped. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
