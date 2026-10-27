# TASK-064: Frontend QA for Sprint 03

- **Backlog item:** BL-014, BL-015, BL-016, BL-052, BL-059, BL-064, BL-065, BL-078; VULN-012
- **Assignee:** qa
- **Status:** TODO
- **Depends on:** TASK-054, TASK-055, TASK-056, TASK-057, TASK-058, TASK-059, TASK-060, TASK-061, TASK-062
- **Estimate:** M

## Description
Test the Sprint 03 screens in a real browser against the live API. Do not fix code. File bugs as `BUG-XXX`.

## Technical Notes
- No local Docker. Frontend via npm, backend via the venv, headless Chrome, same style as Sprint 02 TASK-040.
- Cookie: after login, `localStorage` does not contain `delivery.refresh_token`, and `document.cookie` does not contain the refresh value. Reload keeps the user signed in. Logout returns to login and a later refresh does not restore the session.
- Walk each role's home, then: change password, profile edit, forgot-password (same confirmation text and the contact-admin line), reset-password with a token taken from the dev email backend, approval queue, users list filters, activate/deactivate, create and delete.
- Manager: the create form has no Admin role, and an Admin row has no activate, edit-save, or delete control. Confirm the API also returns 403 if the request is forced.
- Rejected and pending login messages. Arabic and English on one new form (BL-064) and on the shell.
- Empty approvals list, a forced failed load with retry, and an offline message (BL-065).
- axe-core on the new screens, same budget as Sprint 02 (0 violations).
- Production PWA install and the service-worker rebuild stay out of scope (Sprint 01 E2 and QA N-20).

## Acceptance Criteria
- [ ] Frontend section of `QA_REPORT.md` records pass/fail per screen
- [ ] The refresh token is not in localStorage or `document.cookie` after login
- [ ] BR-14 is checked in the UI and with one forced API call
- [ ] No code fixes by QA

## Activity Log
- 2026-10-26 — team_leader: Task created.
