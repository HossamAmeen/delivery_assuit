# TASK-060: Create, edit, and delete a user

- **Backlog item:** BL-059; BR-14
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-054, TASK-059
- **Estimate:** M

## Description
Admin and Manager create a user, edit one, and delete one, with Manager blocked from Admin accounts in the UI as well as by the API.

## Technical Notes
- Routes: `/admin/users/new` (`user-create`) and `/admin/users/:id` (`user-edit`), same roles as the list.
- Create form: full name, phone, username, email, password, role. Role options are admin, manager, driver, trader, client. When the actor is a Manager, the Admin option is absent. Submit `POST /users/` and then go to the list.
- Edit form: same fields except password is optional (blank means "leave it"). Role select follows the same Manager rule. Load `GET /users/{id}/`. Also show `rejection_reason` and `last_action` as read-only text when present. Save `PATCH /users/{id}/` with only dirty fields, and never send `status`.
- Delete asks for a confirmation, then `DELETE /users/{id}/`, then returns to the list. Hide delete when the row is the signed-in user, and when a Manager is looking at an Admin.
- Field errors from the server render on the fields. A 403 shows the server message and leaves the form data in place.
- Do not send `is_staff` or `is_superuser`.

## Acceptance Criteria
- [x] Admin can create an Admin; Manager's create form has no Admin role
- [x] Edit saves and shows the last action
- [x] Delete confirms, then the user disappears from the list
- [x] A 403 or a field error is visible and the form is not cleared
- [x] Vitest covers the Manager role list and a validation error

## Activity Log
- 2026-10-26 — team_leader: Task created for the write side of BL-059.
- 2026-10-27 — frontend: Routes `/admin/users/new` (`user-create`, registered before the id route) and `/admin/users/:id` (`user-edit`, numeric id) under the admin area. Create form: name, phone, username, email, password, role; a Manager's role list has no Admin option; username is required for admin and manager; submit calls `POST /users/` (never `status`, `is_staff`, or `is_superuser`) and returns to the list. Edit form: loads `GET /users/{id}/`, shows status, rejection reason, and last action (who, when, reason) as text, and sends only the changed fields (a blank password is left out). A Manager opening an Admin gets a read-only form with no save or delete; delete is also hidden on your own row and your own role is locked (the API refuses it). Delete asks for confirmation, then `DELETE /users/{id}/` and returns to the list. Field errors show on the fields, a 403 shows the server message, and neither clears the form. Arabic and English strings added. 16 new Vitest tests; suite 254 passed; eslint clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
