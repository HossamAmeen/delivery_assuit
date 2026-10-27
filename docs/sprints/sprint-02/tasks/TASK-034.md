# TASK-034: Auth API service, token handling and Pinia auth store

- **Backlog item:** BL-012, BL-013
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-027
- **Estimate:** M

## Description
Frontend plumbing for sessions. Decision (Team Leader, flag for Security): access token kept in memory only; refresh token in `localStorage` so the user stays signed in after a page refresh. No `v-html` anywhere (already enforced by lint).

## Technical Notes
- `src/api/auth.js` (login, register*, refresh, logout, me), `src/stores/auth.js` (user, tokens, status, `isAuthenticated`, `homeRoute`), restore session on app start via refresh.
- Axios interceptors in `http.js`: attach `Authorization: Bearer`, on 401 try one refresh (single in-flight promise), retry the request, otherwise clear the session and go to login. Store the rotated refresh token each time.
- Handle 403 `account_pending` / `account_deactivated` codes as typed errors for the UI.
- All user-visible messages through i18n; server `message` shown as returned.

## Acceptance Criteria
- [x] Session survives a page refresh until logout or refresh failure
- [x] Concurrent 401s trigger a single refresh
- [x] Unit tests with mocked API (login, restore, refresh rotation, failure)
- [x] Lint clean; tests passing
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-15 — frontend: Implemented src/api/auth.js, src/stores/auth.js, http.js interceptors (bearer, single-flight refresh, retry once, typed `code`), src/utils/authErrors.js, i18n keys auth.errors.*, main.js wiring (init + restore). tests/unit/auth.spec.js added; full suite 72 passed, eslint clean. Status -> IN_REVIEW.
- 2026-10-16 — security: Reviewed. VULN-012 (refresh token in localStorage, no CSP) relates to this task; see ../SECURITY_REPORT.md.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results (frontend)" (TASK-040 APPROVED, retest 120/120 on 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
