# QA Report — Sprint 03

Partial report. Sprint 03 is in progress. This section covers only the cookie session work (TASK-045 and TASK-054). Later tasks are added as they reach QA.

## Summary
- Tasks tested: 2 | Passed: 2 | Failed: 0
- Backend suite: 298 passed, ruff clean
- Frontend: Vitest all passed, eslint clean
- Live backend black-box (`qa/cookie_blackbox.py`): 41/41 PASS
- Live browser run in headless Chrome (`qa/frontend_cookie.mjs`): 24/25 PASS; the one miss is BUG-010 (Low)

## Results
| Task | Item | Result | Notes |
|------|------|--------|-------|
| TASK-045 | BL-012, BL-013, VULN-012, VULN-017 (reuse half) | PASS | Cookie flags, JSON has no refresh token, Origin check, reuse revokes all of the user's tokens, logout idempotent, CORS exact-origin with credentials. |
| TASK-054 | BL-012, BL-013, VULN-012 | PASS (BUG-010 Low open) | Nothing in localStorage or `document.cookie`, reload restores the session, logout clears the cookie. |

## What was checked
**Backend (against the contract, live server, fresh SQLite)**
- Login sets `delivery_refresh` with HttpOnly, SameSite=Strict, Path `/api/v1/auth/`, Max-Age 7 days, no Domain, not Secure in dev. No `refresh` anywhere in the JSON.
- Refresh returns `data.access` only and sets a new cookie. A `refresh` field in the body is ignored (401 without the cookie).
- Origin check: missing, foreign, wrong port, wrong scheme, trailing slash, `null`, and look-alike host all give 403 `origin_rejected`. The cookie is not rotated and nothing is blacklisted. Login does not need Origin.
- Reuse: an old token gives 401, clears the cookie and revokes the user's other outstanding tokens. A fresh login works. Another user's tokens are unaffected.
- Logout: contract body, cookie cleared, token blacklisted, idempotent with missing, junk or already-blacklisted cookies, works with an invalid bearer attached, and logout with the token only in the body does not blacklist it.
- CORS preflight: exact allowed origin with credentials true. An evil origin gets no Allow-Origin.
- A deactivated account cannot refresh (401). Eight parallel refreshes of one token give at most one 200 and no 500 (SQLite limit is documented).

**Frontend (real Chrome, page and API on 127.0.0.1)**
- Login: no refresh token or JWT in storage, `document.cookie` empty, the browser holds the HttpOnly Strict cookie.
- Reload restores the session through refresh then `/auth/me/`, the refresh body carries no token, and the role guard still works.
- A leftover `delivery.refresh_token` is removed at startup and never sent.
- Logout goes to `/login`, the cookie is cleared, and a reload does not restore the session. Logout still signs out locally when the logout call fails.
- A first visit without a cookie shows no "session expired" message.
- A deactivated account returns to `/login` on reload. A page from a non-allowlisted origin cannot use the cookie.

## Not covered (belongs to other tasks)
- Over-long login fields (TASK-053) and `Cache-Control` on auth responses (TASK-053).
- Password change, reset and deactivation revoking tokens (TASK-046, 048, 050).
- PostgreSQL strict "exactly one 200" race (Sprint 02 E1, not required to ship this sprint).
- Real HTTPS with `Secure` set (production setting; covered by unit tests only, not run over TLS here).

## Bugs
### BUG-010: No "session expired" notice after a reload when the session was ended elsewhere
- **Severity:** Low
- **Task:** TASK-054
- **Steps to reproduce:** 1. Sign in as a driver. 2. Log that session out from another client (for example a second device) so the refresh token is blacklisted. 3. Reload the first tab.
- **Expected:** `/login` with the "session expired" notice. This is what Sprint 02 check BL012-11 verified when the token sat in localStorage.
- **Actual:** `/login` with no notice. The user lands on the login form with no explanation. The redirect itself and the cleared state are correct, so this is not a security issue.
- **Cause:** The browser can no longer tell "had a session" from "never signed in", because the cookie is HttpOnly. TASK-054 deliberately shows no notice on the first restore failure.
- **Suggested fix (Frontend decision):** keep a non-secret `localStorage` flag such as `delivery.has_session=1` set at login and cleared on logout, and show the notice only when the flag is set. It holds no token.
- **Status:** OPEN. Does not block the task (backlog line 851 only requires the redirect).

## QA Sign-off (TASK-045 and TASK-054 only)
- **Status:** APPROVED
- **Date:** 2026-10-27
- **Open bugs:** BUG-010 (Low)
- **Notes:** QA passes both tasks. VULN-012 and the reuse half of VULN-017 are closed only after the Security retest of the cookie path.
