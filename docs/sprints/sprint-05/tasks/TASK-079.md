# TASK-079: Browse shops and shop details for clients

- **Backlog item:** BL-045, BL-046
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-067, TASK-068
- **Estimate:** M

## Description
`GET /shops/` and `GET /shops/{id}/` for clients, using `is_shop_orderable` and `pickup_locations`.

## Technical Notes
- No phone in any shop payload
- Hidden or deleted items never returned

## Acceptance Criteria
- [x] Only orderable shops are listed and searchable by name
- [x] A closed or location-less shop is 404
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — backend: Built GET /api/v1/shops/ (search by name, sorted, paginated) and GET /api/v1/shops/{id}/ (visible non-hidden items with price null, pickup locations default first) for clients only. Orderable rule exists as one queryset (orderable_shops) and one helper (is_shop_orderable), tested to agree. Closed, location-less, or non-active-trader shops are 404/absent. No phone in any payload. 26 tests. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
