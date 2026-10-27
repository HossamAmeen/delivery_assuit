# TASK-058: Approval queue and rejected login

- **Backlog item:** BL-078
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-054
- **Estimate:** M

## Description
Admin and Manager see pending driver and trader registrations and approve or reject them. A rejected person sees that state on the login screen.

## Technical Notes
- Route `/admin/approvals`, name `approvals`, under `AdminLayout`, roles `admin` and `manager` only. Add a nav link in the admin shell.
- Load `GET /users/?status=pending_approval`. Show name, phone, role, and email. Empty list is an empty state (wording can be finished in TASK-062; this task still must not render a blank page with no message).
- Approve calls `POST /users/{id}/approve/`. Reject asks for an optional reason, then `POST /users/{id}/reject/` with `{ reason }`. Remove the row on success. Show the server error if the call fails.
- A driver, trader, or client who opens the URL is sent to their own home by the existing role guard.
- Login: handle new code `account_rejected` in `ERROR_CODES` and `LoginView`. Show the server `message` (it may contain the reason). Do not send them into the app.
- Pending login (`account_pending`) stays as it is.

## Acceptance Criteria
- [x] Admin and Manager can open the queue; other roles cannot
- [x] Approve and reject call the contract endpoints and update the list
- [x] Reject can be sent with a reason and with an empty reason
- [x] Login shows the rejected message and stays on the login screen
- [x] Vitest covers the queue actions and the rejected login code

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-078.
- 2026-10-27 — frontend: Route `/admin/approvals` (`approvals`) under `AdminLayout`, roles admin and manager only (the existing guard sends other roles home). `AdminLayout` now has a small nav (dashboard, approvals, users). The queue loads `GET /users/?status=pending_approval` and shows name, role, phone, email; loading, empty message, and error-with-retry states (shared `ListStatus.vue`). Approve calls `POST /users/{id}/approve/`; reject opens an optional reason box and calls `POST /users/{id}/reject/` with the trimmed reason (empty is fine); the row is removed on success and a server error is shown without removing it. Login handles `account_rejected`: shows the server message (it carries the reason), stays on login, no session. New `api/users.js` holds every staff endpoint for the next tasks. Arabic and English strings added. 15 new Vitest tests; suite 226 passed; eslint clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
