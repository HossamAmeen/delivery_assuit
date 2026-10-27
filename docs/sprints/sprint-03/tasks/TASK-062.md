# TASK-062: Loading, empty, error, and offline states

- **Backlog item:** BL-065
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-055, TASK-056, TASK-057, TASK-058, TASK-059, TASK-060
- **Estimate:** M

## Description
The new screens tell the user when data is loading, when a list is empty, when a request failed, and when the browser is offline.

## Technical Notes
- Screens: profile, approvals, users list, user detail/edit. Forms that only submit (change password, forgot password, reset password, create user) need a disabled submit and a visible busy label while the request is in flight, plus the error state from TASK-061.
- Lists (approvals, users): a loading indicator that is not the empty message, an empty message when `count` is 0, and an error message with a retry button when the load fails.
- Offline: when `ApiError.isNetworkError` is true, show a connection message and retry. Listen to `offline` / `online` only to refresh that message; do not block the UI forever after it comes back.
- An expired session (401 after a failed refresh) still goes to login. If a form is dirty, keep the typed values in the component until navigation; do not wipe them before the redirect. A full reload may lose them; that is acceptable.
- Reuse one small presentational component if it stays simple. Do not add a new design system.

## Acceptance Criteria
- [x] Approvals and the users list each have loading, empty, and error-with-retry states
- [x] Profile shows loading and a retryable error
- [x] A network failure shows the offline message and retry runs the same request again
- [x] A failed refresh during an edit does not clear the fields before leaving the page
- [x] Vitest covers empty, error+retry, and the network error

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-065.
- 2026-10-27 — frontend: Built. `useOnline` composable; `ListStatus` follows the browser offline/online events and retries once on reconnect; Profile and user detail now use `ListStatus` (loading, offline, retry). Approvals and users list already had the states. Typed values stay after a failed save. `tests/unit/states.spec.js` added. Vitest 277 passed, eslint and prettier clean, vite build ok. Not run in a browser. Status IN_REVIEW; QA paused until staging upload.
