# TASK-059: Users list, activate, and deactivate

- **Backlog item:** BL-052, BL-059
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-054, TASK-058
- **Estimate:** M

## Description
Admin and Manager see every user, filter them, and activate or deactivate accounts that are not Admins when the actor is a Manager.

## Technical Notes
- Route `/admin/users`, name `users`, roles `admin` and `manager`. Nav link next to approvals.
- `GET /users/` with `page`, `role`, `status`, and `search`. Controls for those filters. Pagination uses `data.next` / `data.previous` or the page number the contract shows; do not invent a different list shape.
- Columns: name, phone, role, status. Row click goes to `/admin/users/:id` (the edit screen is TASK-060; this task may render a read-only detail if TASK-060 is not merged yet, but the route should exist).
- Activate and deactivate buttons call `POST /users/{id}/activate/` and `POST /users/{id}/deactivate/`. Hide them when the row's status is not `deactivated` or `active` respectively. When the signed-in user is a Manager and the row's role is `admin`, hide the buttons and do not call the API.
- Show the server 403 message if a click still fails.
- Bilingual. Status and role use the existing i18n keys where they exist; add `rejected`.

## Acceptance Criteria
- [x] The list loads, filters, searches, and pages
- [x] Activate and deactivate update the row's status
- [x] A Manager does not see those actions on an Admin row
- [x] A non-admin role cannot open the route
- [x] Vitest covers the filter query and the hidden Admin actions

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-052 and the list half of BL-059.
- 2026-10-27 — frontend: Route `/admin/users` (`users`) under the admin area, roles admin and manager (nav link next to approvals). Loads `GET /users/` with page, role, status, and search (empty filters are not sent; a filter change returns to page 1 after a short pause); previous/next use the contract's `next`/`previous`. Columns: name (link to `/admin/users/:id`), phone, role, status. Activate shows only for deactivated rows and deactivate only for active rows (never on your own row); a Manager sees no buttons on an Admin row, so the API is not called. A failed click shows the server message and leaves the row as it was. Loading, empty, and error-with-retry states. `rejected` added to the status strings. The detail route itself is added by TASK-060 in the same batch. 12 new Vitest tests; suite 238 passed; eslint clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
