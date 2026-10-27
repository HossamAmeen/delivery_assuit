# TASK-056: Profile screen

- **Backlog item:** BL-015
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-054
- **Estimate:** M

## Description
A signed-in user can see their profile and edit their name, phone, and email. Role and status are visible and not editable.

## Technical Notes
- Route `/account/profile`, name `profile`, any authenticated role. Link it from the user menu next to change password.
- Load with `GET /auth/me/`. Show name, phone, username, email, role, and status. Username, role, and status are text, not inputs.
- Save sends `PATCH /auth/me/` with `full_name`, `phone`, and `email` only. Empty email is allowed (the user is clearing it).
- Field errors from the server (`phone`, `email`, `full_name`) show beside the fields. A success message confirms the save and the store's `user` is updated so the header name stays in sync.
- Bilingual labels. Phone input accepts the same characters the API normalises (spaces, dashes, Arabic-Indic digits).
- The user menu currently shows `full_name` from login. After a profile save, that name updates without a second login.

## Acceptance Criteria
- [x] The screen shows the contract fields and refuses to offer role or status as inputs
- [x] A duplicate phone or email shows the server message on that field
- [x] Saving a new name updates the header
- [x] A user never sees another user's profile
- [x] Vitest covers load, save, and a field error

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-015.
- 2026-10-27 — frontend: Route `/account/profile` (`profile`, any signed-in role) and a user-menu link. Loads `GET /auth/me/` through the auth store with a loading state and a retryable error. Shows username, role, and status as text; only full name, phone, and email are inputs. Save sends `PATCH /auth/me/` with exactly those three fields (email may be empty) and merges the result into the store, so the header name updates without a new login. Server `errors.full_name/phone/email` show on their fields and the form keeps what was typed; client checks use the shared phone helper (Arabic-Indic digits count). The screen only ever calls `/auth/me/`, so it can show only the caller. Arabic and English strings added (including `statuses.*`). 9 new Vitest tests; suite 199 passed; eslint clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
