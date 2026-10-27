# TASK-051: Users list and detail

- **Backlog item:** BL-059
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-049
- **Estimate:** M

## Description
Admin and Manager can list every user and open one user's details. Nobody else can.

## Technical Notes
- `GET /api/v1/users/` and `GET /api/v1/users/{id}/` as in the contract. Read side only. Writes are TASK-052.
- Queryset: not soft-deleted. `select_related` the actor on `last_action` to avoid N+1. `last_action` is the latest `AccountAction` for that user, or null.
- Filters: `role`, `status` (django-filter, exact). `search` is a single query param, case-insensitive match on `full_name` or `phone`.
- Pagination: existing project pagination, default 20, max 100, newest `id` first if no other order is set. Contract says the Sprint 01 envelope.
- List item fields: `id`, `full_name`, `phone`, `username`, `email`, `role`, `status`. Detail adds `rejection_reason` and `last_action`. Never return a password or hash.
- Permission `IsAdminOrManager`. Manager **sees** Admin rows (the backlog says all users). A client, driver, or trader gets 403. Anonymous gets 401.
- This is the live endpoint QA N-14 asked for. Cover the role matrix in tests: each role allowed or denied.

## Acceptance Criteria
- [x] Admin and Manager receive a paginated list; other roles get 403
- [x] Filter by role and status, and search by name or phone
- [x] Detail shows the profile and the last action, and hides secrets
- [x] Tests written and passing

## Activity Log
- 2026-10-26 — team_leader: Task created for the read side of BL-059.
- 2026-10-27 — backend: `GET /users/` (paginated, newest id first, soft-deleted hidden, Manager sees Admin rows) and `GET /users/{id}/` (profile, `rejection_reason`, `last_action`). Filters `role` and `status` (invalid value is 400) and `search` (name contains, or phone contains when the text is digit-like, so `manager1` does not match every phone with a 1). Admin or Manager only; client, driver, trader get 403, anonymous 401. No secrets in either response. Query count does not grow with rows (tested). 17 new tests; full suite green; ruff clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
