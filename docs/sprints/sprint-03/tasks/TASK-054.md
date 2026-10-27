# TASK-054: Cookie session in the browser

- **Backlog item:** BL-012, BL-013; VULN-012
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-044
- **Estimate:** M

## Description
The browser stops storing the refresh token. Login, refresh, and logout use the HttpOnly cookie from the contract. The access token stays in memory.

## Technical Notes
- Read `docs/sprints/sprint-03/API_CONTRACT.md`. If it is missing, stop.
- `frontend/src/api/http.js`: `withCredentials: true` on the axios instance. The refresh interceptor calls `POST /auth/token/refresh/` with an empty body and sends cookies. It reads `data.access` only.
- `frontend/src/stores/auth.js`: delete `REFRESH_STORAGE_KEY` and every `localStorage` read or write of the refresh token. On startup, if that old key exists, remove it. `ensureRestored` still refreshes the session by calling the refresh endpoint (the cookie is sent automatically) and then `GET /auth/me/`.
- `frontend/src/api/auth.js`: login no longer reads `data.refresh`. Logout no longer sends a refresh body.
- Do not add a CSP meta tag. Do turn on ESLint `vue/no-v-html` as an error, and keep the existing rule that user content is rendered with `{{ }}`.
- Update unit tests that mocked a stored refresh token. They should assert localStorage no longer receives one.
- A 403 `origin_rejected` surfaces as a normal session failure and sends the user to login.

## Acceptance Criteria
- [x] After login, `localStorage` has no `delivery.refresh_token` and the refresh cookie is not readable from `document.cookie`
- [x] A full page reload still restores the session via the cookie
- [x] Logout clears the session even when the access token is already expired
- [x] `vue/no-v-html` fails the lint if someone adds `v-html`
- [x] Vitest and eslint pass

## Activity Log
- 2026-10-26 — team_leader: Task created. PO chose the cookie, not CSP.
- 2026-10-26 — frontend: IN_REVIEW. Axios sends credentials. Login, refresh, and logout no longer read or send a refresh token. The access token stays in memory. A leftover `delivery.refresh_token` key is deleted and never sent. The first restore 401 (no cookie) does not show “session expired”; a later refresh failure on a live session still does. `vue/no-v-html` is already `error` in `frontend/eslint.config.js`. Vitest 180 passed, eslint clean. Browser on `http://127.0.0.1:5173` against `http://127.0.0.1:8000`: login 200, `localStorage` key null, `document.cookie` empty, reload restored the client home (refresh 200, me 200), logout 200 returned to login, and the next refresh was 401. QA has not retested this.
- 2026-10-27 — qa: PASS. Backend 298 passed, ruff clean; live black-box 41/41; Vitest and eslint clean; live Chrome run 24/25. BUG-010 (Low, no session-expired notice after a reload when the session was ended elsewhere) is open and does not block. Status DONE for QA. VULN-012 is not closed until the Security retest of the cookie path. See QA_REPORT.md.
