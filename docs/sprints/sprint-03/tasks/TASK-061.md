# TASK-061: Field validation and clear errors

- **Backlog item:** BL-064
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-055, TASK-056, TASK-057, TASK-058, TASK-060
- **Estimate:** S

## Description
Every new form shows a field-level error for missing or invalid input, in Arabic and English, and a friendly message when the server fails unexpectedly.

## Technical Notes
- Forms in scope: change password, profile, forgot password, reset password, reject reason, user create, user edit.
- Required fields are marked and blocked on submit with a localised message, before the request, when the contract says the field is required.
- Phone fields share one client check: after stripping spaces and dashes, 8 to 15 digits (Arabic-Indic digits count). The server remains the authority; a server `errors.phone` still replaces the client message.
- Map a body-less 500 or a network error to the existing generic friendly message. Never render a stack trace or a raw JSON blob.
- Switch the UI language and confirm the client-side messages follow it. Server messages stay in the language of `Accept-Language` (already sent by `http.js`).
- Do not restyle unrelated Sprint 02 forms except where they share a helper you extract. Registration and login already show field errors; leave them unless the shared phone helper fixes a real gap.

## Acceptance Criteria
- [x] Each new form shows a field error for an empty required field without calling the API
- [x] A server `errors` payload is shown on the matching field
- [x] An unexpected 500 shows the generic message only
- [x] Arabic and English client messages both exist
- [x] Vitest covers one form in each language and one 500

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-064.
- 2026-10-27 — frontend: Shared helpers in `utils/forms.js` (one phone check: 8–15 digits after removing spaces/dashes, Arabic-Indic and Persian digits count; email check; server-error mapper; friendly-message mapper). Every new form (change password, profile, forgot, reset, reject reason, user create, user edit) blocks an empty required field before any request, marks required fields, and shows a server `errors` payload on the matching field (a too-long reject reason shows beside the box). Client messages are stored as keys, so a message already on screen follows a language switch; server messages stay in the language the API returned. A 5xx, a body-less error, or a network failure shows only the generic or connection message (no server text, no JSON). Login and registration are unchanged. English and Arabic key sets are checked to be identical by a test. 15 new Vitest tests; suite 269 passed; eslint clean; `vite build` succeeds. Status IN_REVIEW. Not QA-tested (QA paused by PO).
