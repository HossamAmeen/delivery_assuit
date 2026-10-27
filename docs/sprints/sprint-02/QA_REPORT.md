# QA Report — Sprint 02

## Summary
- **Backend (TASK-039): APPROVED** after retest on 2026-10-16. BUG-007 is fixed and verified. No open bugs.
- Backend suite: **293 passed** (retest; 291 in the first run), coverage **96%** overall (target 80%). New account code is at 99-100% (`views`, `serializers`, `permissions`, `authentication`, `managers`, `phone`, `models`: 100%; `services`: 99%).
- Black-box run against a live dev server (venv, fresh SQLite DB, no Docker): **100/100 PASS** (retest 2026-10-16; the first run was 97/100, the 3 failures were BUG-007).
- Frontend (TASK-040): DONE (retest 2026-10-16), 120/120 cases PASS, axe 0 violations, BUG-008 and BUG-009 VERIFIED, no open bugs; see the Frontend section at the end.
- Bug numbering continues from Sprint 01 (BUG-001..006); frontend bugs are BUG-008 and BUG-009.

## How it was tested
1. Full suite with coverage: `backend/.venv/bin/python -m pytest --cov --cov-report=term`.
2. `qa/accounts_blackbox.py` (extends the Sprint 01 scripts): real `runserver` on a fresh SQLite DB, `DEBUG=False`, using the contract and backlog criteria as the oracle. Run with
   `python3 docs/sprints/sprint-02/qa/accounts_blackbox.py <backend_dir> <python>`. Output saved in `qa/accounts_blackbox.out`.
   - Phase A: throttles relaxed, functional cases. State changes (deactivate, pending, soft-delete) done through `manage.py shell`.
   - Phase B: default throttles (auth 10/min, sensitive 30/min) with `NUM_PROXIES=0` and `=1` and forged `X-Forwarded-For`.
3. All servers started by QA were stopped (`pgrep runserver` empty).
4. Role matrix on non-production URLs (a role-restricted action exists only in a test URLconf) is covered by `apps/users/tests/test_permissions.py`; live, `GET /auth/me/` is checked for all five roles.

## Traceability: acceptance criteria to cases

### BL-008 Roles and role-based access
| Criterion | Cases | Result |
|---|---|---|
| Every account has exactly one of the five roles | BL008-2/admin, manager, driver, trader, client (live `/me`); DATA-2 | PASS |
| Admin = Manager, except Manager cannot manage Admin accounts (BR-14) | `test_permissions.py` (`can_manage_account` matrix) | PASS (suite; no user-management endpoint exists yet, so not testable live) |
| Other role's features refused with a clear "not allowed" | `test_permissions.py` role matrix (each role allowed and denied) | PASS (suite) |
| Unauthenticated reach only register, login, refresh, logout (recovery later) | BL008-1, 1b, 7, 10, 11, R1 (`/me` 401, junk token 401, refresh/access token misuse 401, no admin/manager register route 404) | PASS |
| Status checked on every request | BL008-3, 4, 5, 6 (deactivated: 403 `account_deactivated`; pending: 403 `account_pending`; re-activated token works again; soft-deleted refused) | PASS |
| Role and status cannot be set by the client | BL008-MA1, MA2, MA3 (body `role`, `status`, `is_staff`, `is_superuser`, `username`, `id` ignored) | PASS |
| Tests for each role allowed/denied incl. Manager vs Admin | suite | PASS |

### BL-009 Driver registration / BL-010 Trader / BL-011 Client
| Criterion | Cases | Result |
|---|---|---|
| Only name, phone, password required; clear field errors; email optional | BL009-4, 6; BL009-5/5b/5c, 9, 9b | PASS |
| Duplicate phone rejected (any formatting, all three roles) | BL009-2/driver, trader, client | PASS |
| Weak password rejected with clear message | BL009-3, 3b, 3c, 3d | PASS |
| Driver and Trader: role set, `pending_approval`; Client: `active` | BL009-1, BL010-1, BL011-1, BL009-1b | PASS |
| Phone normalised (+20, dashes, Arabic-Indic digits) | BL010-1, BL011-1 | PASS |
| Email validation and uniqueness | BL009-7, 8 | PASS |
| Robustness (malformed JSON, list/dict values, GET, HTML in name) | BL009-11, 12, 13, 14 | PASS |
| No tokens or password in response; password hashed | BL009-1, 10 | PASS |
| Arabic messages | I18N-1, I18N-2 | PASS |

### BL-012 Login
| Criterion | Cases | Result |
|---|---|---|
| Phone or username accepted (phone in any format) | BL012-1, 2, 3, 4, 5 | PASS |
| Success returns tokens + user summary with role (for the home screen) | BL012-1..5 | PASS |
| Invalid credentials generic; no existence leak in body | BL012-8 (wrong pw on pending / deactivated / unknown: identical 401 body) | PASS |
| Invalid credentials: no existence leak in timing | BL012-12 (median of 12 requests: unknown 845 ms, existing 857 ms, pending 839 ms) | PASS |
| Soft-deleted account looks like unknown | BL012-11, BL008-6 | PASS |
| Pending: 403 `account_pending`, friendly message, no tokens, only after correct password | BL012-6, 6b | PASS |
| Deactivated: 403 `account_deactivated`, friendly message, no tokens | BL012-7 | PASS |
| Pending/deactivated messages in Arabic | BL012-9, 9b | PASS (retest; first run FAIL, BUG-007) |
| Failed attempts rate-limited | RATE-A1..A5 (11th request 429, envelope, Retry-After, Arabic 429, correct password also blocked, refresh/logout share the bucket) | PASS |
| Spoofed `X-Forwarded-For` does not help | RATE-A6, RATE-S1, RATE-P1, RATE-P2 | PASS |
| Stays signed in across refresh (backend part) | BL013-1, 3 (rotation works, new refresh usable); frontend part in TASK-040 | PASS (backend) |
| Deactivated / pending / soft-deleted accounts cannot refresh | BL012-13, 14, 15 | PASS |
| Missing field | BL012-10 | PASS |

### BL-013 Logout
| Criterion | Cases | Result |
|---|---|---|
| Logout blacklists the refresh token, response per contract, works without Authorization header | BL013-5 | PASS |
| Previous session cannot call protected actions (refresh dead) | BL013-6 | PASS |
| Rotation: old refresh rejected, new refresh works and rotates again | BL013-1, 2, 3 | PASS |
| Idempotent (twice, and with an already-rotated token) | BL013-7, 7b | PASS |
| Validation: missing refresh, junk token, access token as refresh | BL013-8, 9, 9b | PASS |
| One session's logout does not kill another session | BL013-10 | PASS |
| Access token stays valid until expiry (documented contract behaviour, max 15 min) | BL013-11 | PASS (as documented) |
| Wrong method | BL013-12 | PASS |
| Arabic logout message | I18N-3 | PASS (retest; first run FAIL, BUG-007) |
| Arabic invalid-refresh 401, `/me` 401 | I18N-4, I18N-5 | PASS |

### BL-007 follow-up (TASK-033 seed_demo)
| Case | Result |
|---|---|
| T033-1 seed ok, password not printed | PASS |
| T033-2 run twice: identical user set, no duplicates | PASS |
| T033-3 each status represented | PASS |
| T033-4 active driver and trader, pending driver, deactivated client present | PASS |

### Data and migrations
| Case | Result |
|---|---|
| SETUP-1 migrate on empty DB including `token_blacklist` | PASS |
| DATA-1 `makemigrations --check` clean | PASS |
| DATA-2 every self-registered account has a phone | PASS |
| DATA-3 no duplicate phones | PASS |

## Task results
| Task | Item | Result | Notes |
|------|------|--------|-------|
| TASK-027 | BL-008..013 | PASS | Contract matched live behaviour in every case, apart from the Arabic wording of three messages (not part of the contract by design, see BUG-007). |
| TASK-028 | BL-008..011 | PASS | Status, phone normalisation, migration. |
| TASK-029 | BL-008 | PASS | `/auth/me/`; pending gets 403 (PO decision recorded in the task). |
| TASK-030 | BL-009..011 | PASS | |
| TASK-031 | BL-012 | PASS | Arabic 403 messages fixed (BUG-007 closed). |
| TASK-032 | BL-013 | PASS | Arabic logout message fixed (BUG-007 closed). |
| TASK-033 | BL-007 | PASS | |
| TASK-039 | QA | PASS | Backend QA done; BUG-007 retested and closed. |

## Bugs
### BUG-007: Three new messages have no Arabic translation
- **Severity:** Medium
- **Task:** TASK-031 (pending/deactivated messages), TASK-032 (logout message)
- **Steps to reproduce:** 1. Seed demo data. 2. `POST /api/v1/auth/token/` with `Accept-Language: ar` and `{"username_or_phone":"demo_driver_pending","password":"<DEMO_PASSWORD>"}`. 3. Same for `demo_client_deactivated`. 4. Log in normally, then `POST /api/v1/auth/logout/` with `Accept-Language: ar` and the refresh token.
- **Expected:** Arabic messages (BL-006; TASK-031 says "friendly bilingual messages"; BL-012 says deactivated users are told why in a friendly message).
- **Actual:** Responses are in English: "Your account is pending approval. You will be able to log in once an administrator approves it.", "Your account has been deactivated. Please contact the administrator.", "Logged out successfully." The `msgid`s are not in `backend/locale/ar/LC_MESSAGES/django.po` (the registration success message and the others are). The `code` field is correct, so the frontend can still show its own Arabic text by `code`, but the API text is wrong for Arabic users and the frontend must not rely on it.
- **Status:** CLOSED (2026-10-16 QA retest: BL012-9, BL012-9b, I18N-3 PASS on a live server; full black-box 100/100; suite 293 passed, 96%; spot check of logout with a bad token in Arabic returns 400 with "الرمز غير صالح." and English still "Invalid token."). Backend note:  Added Arabic entries for the 3 messages plus "Invalid token." to django.po, recompiled django.mo, added 2 Arabic tests in apps/users/tests/test_auth.py. Suite 293 passed, ruff clean.)
- **Fix hint (for backend):** add the three entries to the `.po`, recompile `.mo`, and add an Arabic test for each (the existing suite has Arabic checks only for registration).

## Notes (not bugs)
- **N-12 (info):** the duplicate-phone message reveals registered numbers, as required by BL-009..011 and accepted in the contract; it is rate-limited (31st registration per minute per IP gets 429, forged `X-Forwarded-For` does not help).
- **N-13 (info):** login timing is about 850 ms on this machine (real password hasher, intentional dummy hash for unknown users); no measurable difference between unknown, existing and pending identifiers.
- **N-14 (limit of coverage):** the role matrix (each role allowed/denied on a role-restricted action) and `can_manage_account` (Manager vs Admin) are only testable through the test-only URLconf in the suite because no role-restricted production endpoint exists yet. They pass; re-test live once Sprint 03 adds user management.
- **N-15 (info):** the DB-level checks in this run used a dev SQLite database; PostgreSQL behaviour of the migration `0002_user_status` (unique phone with NULLs, username now nullable) was not run (no Docker). Worth a check in staging.
- **N-16 (info):** access tokens issued before a logout remain valid until they expire (max 15 minutes); this is the documented contract behaviour (BL013-11).

## QA Sign-off (backend, TASK-039)
- **Status:** APPROVED
- **Date:** 2026-10-16
- **Open bugs:** none (BUG-007 closed after retest)
- **Notes:** All acceptance criteria for BL-008..BL-013 are met on the backend. Retest: live server (venv, fresh SQLite, DEBUG=False, no Docker, servers stopped afterwards), black-box 100/100, suite 293 passed with 96% coverage. Frontend QA (TASK-040) and the final sprint sign-off are still pending.

---

# Frontend (TASK-040)

## Summary (frontend)
- **Result: PASS after retest (no open bugs).** First run: 117/120 PASS, 3 FAIL (BUG-008 Low, BUG-009 Medium). Retest after the fixes: **120/120 browser cases PASS**; axe-core 60 runs (15 screens/states x en/ar x 360/1280px), **0 violations** (WCAG 2.0/2.1/2.2 A+AA and best-practice). BUG-008 and BUG-009 are VERIFIED.
- Real headless Chrome (puppeteer-core) against a live backend (venv, fresh SQLite, `DEBUG=False`, `seed_demo`, relaxed throttles except the 429 cases) and the Vite dev server. No Docker. Frontend source and backend source were not touched.
- Bug numbering continues after BUG-007.

## How it was tested
- Scripts (extend Sprint 01): `qa/frontend_lib.mjs` (servers, helpers), `qa/frontend_browser.mjs` (functional, guard, session, RTL, keyboard, security hygiene), `qa/frontend_axe.mjs`. Outputs: `qa/frontend_browser.out`, `qa/frontend_axe.out`.
- Run: `BACKEND_DIR=<backend> BACKEND_PY=<venv python> FRONTEND_DIR=<frontend> PUPPETEER_DIR=<dir with node_modules/puppeteer-core> AXE_DIR=<dir with node_modules/axe-core> node docs/sprints/sprint-02/qa/frontend_browser.mjs` (same for `frontend_axe.mjs`).
- Each case uses an isolated browser context (own localStorage). Viewport 360x700 (also 1280x800); Arabic via the app's own language switcher / stored `locale`.
- All servers started by QA were stopped afterwards (no `runserver` or `vite --port 5174` left from this project).
- Not covered: production build (`vite preview`, PWA service worker) was not re-run so as not to overwrite `frontend/dist`; Sprint 01 PWA checks are unaffected by this sprint's code but should be part of the final regression.

## Traceability: acceptance criteria to cases

### BL-012 Login (TASK-036, TASK-035, TASK-038)
| Criterion | Cases | Result |
|---|---|---|
| Phone or username accepted; each role goes to its own home (admin, manager, driver, trader, client; title, name and role shown) | BL012-1 (10 combos: 5 roles x username/phone) | PASS |
| Pending account: friendly message, no session | BL012-2, BL012-6 | PASS |
| Deactivated account: friendly message, no session | BL012-3, BL012-13 | PASS |
| Wrong password / unknown user: same generic message, password cleared | BL012-4, BL012-5 | PASS |
| Client-side required validation, Enter submits, show/hide password, disabled while submitting, link to registration | BL012-7, A11Y-K1, BL012-8, BL012-9, BL012-10 | PASS |
| 429 and network errors have friendly localized messages (en, ar) | BL012-14 en/ar, BL012-15 en/ar | PASS |
| Pending / deactivated / invalid messages in Arabic | I18N-L1, I18N-L2 | PASS |
| Session ended elsewhere or account deactivated while signed in: back to login with a notice, storage cleared | BL012-11, BL012-12 | PASS |
| Stays signed in across a page refresh (frontend part) | BL013-2, BL013-3, BL013-4, BL013-5 | PASS |

### BL-013 Logout (TASK-038)
| Criterion | Cases | Result |
|---|---|---|
| Logout from the user menu goes to login, clears storage | BL013-6 | PASS |
| Old refresh token blacklisted on the server | BL013-7 | PASS |
| Back button / protected URL after logout redirect to login | BL013-8, BL013-9 | PASS |
| Logout works when the API call fails | BL013-10 | PASS |
| User menu usable by keyboard (Enter, Escape returns focus) | A11Y-K2, A11Y-K3 | PASS |
| Only the refresh token is persisted; access token only in memory | BL013-1 | PASS |

### BL-009 Driver / BL-010 Trader / BL-011 Client registration (TASK-037)
| Criterion | Cases (BL009 driver, BL010 trader, BL011 client) | Result |
|---|---|---|
| Chooser, route per role, correct title; trader label "Shop or trader name" | -1 | PASS |
| Missing/invalid fields shown per field, email optional, confirm mismatch | -2, -3, -4 | PASS |
| Client: success note on login, then logs in (phone typed in another format) | BL011-5, BL011-6 | PASS |
| Driver/Trader: pending-approval screen with next steps, no auto-login; cannot log in yet | BL009-5, BL009-6, BL010-5, BL010-6 | PASS |
| Pending screen moves focus to its heading (screen-reader announcement) | BL009-5f, BL010-5f | PASS (retest; was FAIL, BUG-008 VERIFIED) |
| Server errors per field: duplicate phone, weak password, duplicate email (also Arabic) | BL009-7, 8, 9, I18N-R1 | PASS |
| Request carries no role/status/confirm; role comes from the URL | BL009-10 | PASS |
| Arabic name + Arabic-Indic digits accepted | RTL pending 360px | PASS |

### BL-008 Guards and role areas (TASK-035)
| Criterion | Cases | Result |
|---|---|---|
| Anonymous opening any role area goes to /login; 404 and home are public | GUARD-1, 2, 3 | PASS |
| Per role (5 roles): other roles' areas and /login, /register, /register/* redirect to own home | GUARD-4 x5 | PASS |
| Navigation only shows own area; 404 keeps the session | GUARD-5 x5, GUARD-6 x5 | PASS |

### BL-006 Arabic/RTL, 360px, accessibility (all new screens)
| Criterion | Cases | Result |
|---|---|---|
| Login, register chooser, 3 register forms, 4 role homes: en/ar flip, RTL, persists on reload, no overflow/clipping at 360 and 1280 | RTL x18; pending and error states at 360 | PASS |
| Keyboard order and visible focus on login and registration | A11Y-K4 x2 | PASS |
| Focused controls not hidden by the fixed bottom navigation | A11Y-F1 /login | PASS |
| | A11Y-F1 /register/driver (Tab through to "Confirm password" at 360x700) | PASS (retest; was FAIL, BUG-009 VERIFIED) |
| Touch targets >= 44px, labels on every input, error linked by aria-describedby, API error has role=alert | A11Y-T1 x2, A11Y-L1 x2, A11Y-E1, A11Y-E3 | PASS |
| axe: 0 violations on 15 screens/states x en/ar x 360/1280 | frontend_axe.out | PASS |

### Security hygiene (frontend)
| Criterion | Cases | Result |
|---|---|---|
| No token or password in any URL/navigation (6.5k requests inspected) | SEC-1 | PASS |
| No token or password in browser console (300+ messages) | SEC-2 | PASS |
| No JWT/password in vite or backend server logs | SEC-3 | PASS |
| App only talks to its own origin and the configured API | SEC-4 | PASS |
| No uncaught page errors or Vue warnings in the whole run | QUAL-1 | PASS |

## Task results (frontend)
| Task | Item | Result | Notes |
|------|------|--------|-------|
| TASK-034 | BL-012, BL-013 | PASS | Session survives refresh, refresh rotation stored, logout clears and blacklists, token only in memory + refresh in localStorage (flag for Security). |
| TASK-035 | BL-008 | PASS | Guard matrix verified live for all five roles. |
| TASK-036 | BL-012 | PASS | |
| TASK-037 | BL-009..011 | PASS | BUG-008 and BUG-009 fixed and VERIFIED on retest. |
| TASK-038 | BL-012, BL-013 | PASS | |
| TASK-040 | QA | DONE | Retest 120/120, axe 0 violations, no open bugs. |

## Bugs (frontend)
### BUG-008: Pending-approval screen does not move focus to its heading
- **Severity:** Low
- **Task:** TASK-037
- **Steps to reproduce:** 1. Open `/register/driver` (or trader). 2. Fill valid data and submit. 3. After "Registration received" appears, read `document.activeElement`.
- **Expected:** Focus moves to the new `<h1 tabindex="-1">` (the template prepares it for this), so keyboard and screen-reader users are told the screen changed. The status paragraph is inserted together with the section, so it is not reliably announced either.
- **Actual:** Focus stays on `<body>` (the submit button disappeared). Cases BL009-5f, BL010-5f.
- **Status:** VERIFIED (retest 2026-10-16): BL009-5f and BL010-5f PASS, `document.activeElement` is the pending-screen H1 after driver and trader registration.
- **Fix hint (frontend):** after `pending.value = true`, `nextTick` then focus the heading ref.

### BUG-009: Focused registration field is hidden behind the fixed bottom navigation
- **Severity:** Medium (WCAG 2.2 SC 2.4.11 Focus Not Obscured; keyboard users type into a field they cannot see)
- **Task:** TASK-037 (layout from TASK-035)
- **Steps to reproduce:** 1. Viewport 360x700. 2. Open `/register/driver` or `/register/trader`. 3. Press Tab until "Confirm password" is focused. 4. `document.elementFromPoint` at the field centre returns the bottom-nav link (field bottom 686 px, nav top 643 px). Also on `/login` at a 360x400 viewport (on-screen keyboard or landscape) the Sign in button is under the nav. No `scroll-padding-bottom` exists in the CSS.
- **Expected:** Focused controls stay visible (add `scroll-padding-bottom` at least the nav height, or bottom padding on the main area).
- **Actual:** The browser scrolls the field only to the viewport edge, which is under the nav. Case A11Y-F1 /register/driver. A pointer user can still scroll, so it is a keyboard/AT problem; no data loss.
- **Status:** VERIFIED (retest 2026-10-16): A11Y-F1 PASS on /register/driver at 360x700 (Tab order skip-link ... reg-password, toggle, reg-confirm, submit; reg-confirm no longer under the bottom nav) and on /login. `scroll-padding-bottom` present in main.css.

## Notes (not bugs)
- **N-17 (info):** a deactivated account whose session is open is shown "Your session has expired" on the next reload, not the deactivated message, because the refresh endpoint returns the generic 401 for inactive accounts (by contract). Logging in again then shows the deactivated message (BL012-12, BL012-13). Acceptable per contract.
- **N-18 (info):** reloading while the backend is unreachable sends the user to /login but keeps the refresh token in localStorage (so the session returns when the API is back). Consistent with the design decision; flag for the PO if staying on the page with an offline notice is preferred.
- **N-19 (info):** the refresh token lives in `localStorage` (Team Leader decision in TASK-034, flagged for Security). XSS would expose it; there is no `v-html` in the app.
- **N-20 (info):** the production build, PWA/service worker and PostgreSQL were not part of this run (see "How it was tested").

## Retest (2026-10-16)
- Re-ran `qa/frontend_browser.mjs` and `qa/frontend_axe.mjs` the same way as the first run (venv backend with fresh SQLite and `seed_demo`, Vite dev server, headless Chrome, no Docker). Outputs: `qa/frontend_browser.out` (120/120 PASS), `qa/frontend_axe.out` (60 runs, 0 violations). First-run outputs kept as `qa/frontend_browser.run1.out` and `qa/frontend_axe.run1.out`.
- BUG-008: VERIFIED (BL009-5f, BL010-5f). BUG-009: VERIFIED (A11Y-F1 /register/driver incl. Tab to "Confirm password" at 360x700, and /login).
- Regressions: none in the product. One intermediate run showed BL009-10 failing (`qa/frontend_browser.run2_flaky.out`, 119/120). Cause was the QA script: its request listener also caught the CORS preflight (OPTIONS, no body) and sometimes overwrote the captured POST body with an empty string. Verified separately 5 times that the POST body is exactly `full_name, phone, password`. The script now captures only POST requests; the final run is 120/120. Not a product bug.
- All servers started by QA (runserver, vite --port 5174) were stopped; `pgrep` shows none left.

## QA Sign-off (frontend, TASK-040)
- **Status:** APPROVED (task level)
- **Date:** 2026-10-16
- **Open bugs:** none
- **Notes:** All acceptance criteria of BL-008..BL-013 pass in a real browser, BUG-008 and BUG-009 verified. The final sprint sign-off (APPROVAL.md) is not written by this run. Production build / PWA and PostgreSQL remain outside this run (N-20).

---

# Retest: Security fix tasks TASK-041 and TASK-043 (2026-10-17)

Scope: only the two Security fix tasks. The Security retest (JWT-14, THR-1/np1) was NOT run here and APPROVAL.md was NOT written. No code was changed by QA.

## TASK-041 (VULN-011, atomic refresh rotation): DONE (open items below)
How: venv, fresh SQLite, `config.settings.development`, `DEBUG=False`, threaded `runserver`, no Docker. All servers stopped afterwards (`pgrep` empty).

| Criterion | Evidence | Result |
|---|---|---|
| Full backend suite + coverage | `qa/retest_backend_suite.out`: **296 passed**, total coverage 96%, `services.py` 99% (only line 86, the unrelated `seeder` role ValueError branch, is uncovered; it was already uncovered before) | PASS |
| Black-box regression | `qa/accounts_blackbox.py` re-run: **100/100 PASS** (`qa/accounts_blackbox.out`; previous run kept as `accounts_blackbox.run1.out`) | PASS |
| Parallel refresh with one token: never 500 | `qa/refresh_race_live.py` / `.out`: 5 rounds x (10 and 20 threads, barrier-released) = 10 races, 150 requests: only 200/401, **0 x 500** | PASS |
| At most one 200 | every race: exactly 1 x 200, rest 401 (SQLite, threaded runserver) | PASS |
| Old token refused after rotation | RACE-*c: 10/10 races, old token then 401; sequential reuse ROT-3, ROT-5: 401 with the generic error envelope | PASS |
| Winner's new token works | RACE-*d/e: new access works on `/auth/me/`, new refresh rotates again (200), 10/10 races | PASS |
| Rotation and logout unchanged | ROT-1..5 (normal rotation, chain, reuse), LOG-1..5 (logout, refresh after logout 401, idempotent logout, logout with rotated-away token, logout of new token kills it), ERR-1 garbage token 401 | PASS |
| Concurrency test added | dev added deterministic lost-race, DB-error-is-401 and 8-way threaded tests in `apps/users/tests/test_auth.py` (all in the 296 passed); SQLite fallback documented in the task log | PASS (by suite) |

Live script totals: 61 PASS, 0 FAIL.

**Caveats / open items (not bugs):**
- **The strict "exactly one 200 under N parallel refreshes" check is PostgreSQL-only and was NOT run** (no PostgreSQL / Docker locally). On SQLite the live run happened to give exactly one 200 every time, but the contract guaranteed there is only "at most one, never 500". Run it on PostgreSQL (CI or first staging) before relying on the strict guarantee.
- Security retest of JWT-14 (`security/pentest_sprint02.py`) is still pending; it is an acceptance criterion of TASK-041 owned by Security.
- N-21 (info): the `OperationalError -> TokenError (401)` mapping means a loser that hits a DB lock gets 401 instead of 503; acceptable per task notes, but a legitimate client on a busy DB would have to log in again. Not observed in the live run.

## TASK-043 (VULN-013, loopback port bind): DONE by review (open items below)
HARD RULE honoured: docker / docker compose were NOT run. Verified only statically (YAML parsed with PyYAML; files read).

| Criterion | Evidence | Result |
|---|---|---|
| Compose no longer publishes the backend on all interfaces | `docker/staging/docker-compose.yml` parses; `backend.ports == ['127.0.0.1:${BACKEND_PORT:-8000}:8000']`; no other service has `ports:` or `expose:` (db, redis, celery-worker, celery-beat publish nothing); no other compose file under `docker/` or `backend/docker/` publishes ports | PASS (review) |
| Nginx header handling templated | `docker/staging/nginx-proxy-headers.conf`: `proxy_set_header X-Forwarded-For $remote_addr;` (overwrite, not `$proxy_add_x_forwarded_for`), also X-Real-IP, X-Forwarded-Proto, Host; comment says exactly one trusted hop = `NUM_PROXIES=1` and to change both together | PASS (review) |
| Doc note next to the VULN-006 note | `backend/README.md` "Rate limiting behind a proxy": NUM_PROXIES must equal real hops (VULN-006, VULN-013), loopback bind, firewall 80/443 only, overwrite XFF, retest at first deploy. `backend/.env.example` comment at `NUM_PROXIES` repeats the rule | PASS (review) |
| Reviewed by Security; THR-1/np1 from outside the host | Not part of this QA run | DEFERRED |

**Verified by review only:** everything above (YAML structure, text of the snippet and docs). Nothing was executed.
**Deferred to the first staging deploy / other agents:**
- Run THR-1/np1 from outside the host: a forged `X-Forwarded-For` must get 429 after the limit; confirm `ss -ltnp` shows 8000 bound to 127.0.0.1 only and that `ufw`/firewall allows only 80/443 (note Docker-published ports bypass ufw, the loopback bind is the real protection).
- Confirm the real Nginx config actually includes the snippet (the repo has the snippet only; there is no full Nginx site template, so QA cannot verify the include) and that `NUM_PROXIES` in the staging env is 1 (compose default `${NUM_PROXIES:-1}`).
- Gunicorn still binds `0.0.0.0:8000` inside the container (Dockerfile); that is fine only because of the loopback publish and no outer exposure. A containerised Nginx must use the compose network (`backend:8000`), as the compose comment says.
- Security review of the change (acceptance criterion) is still pending.

## Retest result
- No new bugs (no BUG-XXX raised). TASK-041: DONE. TASK-043: DONE. Both with the open items above.
- Artifacts: `qa/refresh_race_live.py`, `qa/refresh_race_live.out`, `qa/retest_backend_suite.out`, `qa/accounts_blackbox.out`, `qa/accounts_blackbox.run1.out`.
