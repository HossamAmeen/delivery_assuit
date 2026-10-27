# TASK-055: Change-password screen

- **Backlog item:** BL-014
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044, TASK-054
- **Estimate:** S

## Description
A signed-in user can change their password from the user menu. After a successful change they are logged out locally and sent to login.

## Technical Notes
- Route `/account/password`, name `change-password`, inside the authenticated area (any role). Add a link in `AppHeader.vue` user menu.
- Form fields: current password, new password, confirm new password. Client checks that the two new values match and that the new value is non-empty before submit. Server errors from `errors.current_password` and `errors.new_password` render next to those fields, in the language the API already returned.
- Call `POST /auth/password/change/` through the auth store, not from the component. On 200, drop the in-memory access token and go to login with a short success message.
- Arabic and English strings in the existing i18n files. Labels, `autocomplete` tokens (`current-password`, `new-password`), and a submit button that can be reached by keyboard.
- Do not invent fields that are not in the contract.

## Acceptance Criteria
- [x] The screen is reachable from the user menu for every role
- [x] A mismatch of the two new passwords is shown without a request
- [x] A server field error is shown on the right field
- [x] Success lands on login and the old session is gone
- [x] Vitest covers the form and the store call

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-014.
- 2026-10-27 — frontend: Route `/account/password` (`change-password`, any signed-in role) and a link in the user menu. Form: current, new, confirm (labels, `current-password`/`new-password` autocomplete, keyboard submit). A mismatch or an empty field is shown without a request; server `errors.current_password` / `errors.new_password` show on those fields; any other failure shows the friendly message (a 500 never shows server text). Success goes through `auth.changePassword`, which calls `POST /auth/password/change/` and then drops the in-memory session, and lands on login with a notice. Shared pieces added for the rest of the sprint: `FormField.vue`, `utils/forms.js`, `api/account.js`, shared form CSS. Arabic and English strings added. 10 new Vitest tests; whole suite 190 passed; eslint clean. Status IN_REVIEW. Not QA-tested (QA paused by PO).
