# QA Report — Sprint 01

## Summary
- Scope tested: **backend** (TASK-021), **frontend** (TASK-022) and the **Docker environment** (TASK-023, run once on 2026-10-10). CI (BL-004) is deferred and untested.
- Frontend: Vitest 47/47, lint clean, build OK; real-browser run (headless Chrome, `qa/frontend_browser.mjs`) **30/30 PASS**.
- Backend tasks verified: TASK-002..009 PASS (TASK-001 contract: backend side confirmed, frontend confirmation pending). Failed: 0.
- Backend suite (repo): 121 passing, coverage 92% (clean-checkout run, 118/121 there only because three compose/docker tests read files outside `backend/`; all pass in the real repo layout).
- Black-box run against a live server on a fresh DB: **42/42 PASS** (`qa/backend_blackbox.py`, repeatable).
- Open bugs: none (BUG-001..006 fixed and verified). No Critical/High. Observations N-5..N-7 below need a PO decision.
- E2E (Playwright): not added (not installed; optional in TASK-022). Equivalent browser checks done with puppeteer-core against real Chrome and the real backend.

## How it was tested
1. Clean copy of `backend/` in an empty directory, new venv, README steps followed literally: `make install-dev`, `cp .env.example .env`, `make check`, `make lint`, `make test`, `make coverage`, `make run` (health call returned 200).
2. `qa/backend_blackbox.py`: real `runserver` on a fresh SQLite DB plus CLI commands; PASS/FAIL per case below. Re-run with `python3 docs/sprints/sprint-01/qa/backend_blackbox.py <backend_dir> <python>`.
3. Contract (`API_CONTRACT.md`) and backlog acceptance criteria used as the oracle, not the code.

## Traceability: acceptance criteria → cases

### BL-001 Backend skeleton
| Acceptance criterion | Cases | Result |
|---|---|---|
| Starts locally, responds on health URL | BL001-1, 2, 4; `make run` + curl | PASS |
| Config from environment; no secrets committed | BL001-14, 17; settings read via env; see BUG-001 and note N-1 | PASS (Low bug) |
| One-command test run, sample test passes | `make test` (121 pass), `make coverage` 92% | PASS |
| API docs reachable in development | BL001-12, 13 | PASS |
| README explains run + tests | README followed literally in a clean directory | PASS |

### BL-007 Admin account and demo data
| Acceptance criterion | Cases | Result |
|---|---|---|
| Documented command creates first Admin without public registration | BL007-1..4, AUTH-1, ADMIN-1 | PASS |
| Optional documented command loads demo data | BL007-5, 9 | PASS for users only; shops, items, locations and orders do not exist yet (known, deferred, in README and docs/TODO.md) |
| Running demo command twice creates no duplicates | BL007-6 | PASS |

### BL-002 Frontend skeleton
| Acceptance criterion | Cases | Result |
|---|---|---|
| Dev server renders a home page | BL002-1 | PASS |
| Routing separates Driver, Trader, Client, Admin/Manager | BL002-2, 3, 4 | PASS |
| Shared API layer, base URL from env, demonstrated by health call | BL002-5, 6, 7 | PASS |
| One-command unit tests, sample passes | `npm test` 47/47 | PASS |
| README explains run + tests | frontend/README.md reviewed | PASS |

### BL-005 Installable PWA shell
| Acceptance criterion | Cases | Result |
|---|---|---|
| Installable with name and icon | BL005-1..4 (Chrome installability check: no errors) | PASS (see note N-6) |
| Opens full-screen, no browser chrome | manifest `display: standalone` verified (BL005-3); actual standalone launch not performed | NOT VERIFIED |
| Usable on a phone-size screen | A11Y-3, BL006-2 at 360px | PASS |

### BL-006 Bilingual support
| Acceptance criterion | Cases | Result |
|---|---|---|
| All screens in Arabic (RTL) and English (LTR), correct layout | BL006-2 on `/`, 4 areas, 404 at 360px and 1280px | PASS |
| Language switch remembered | BL006-2 (reload keeps language and direction) | PASS |
| No hard-coded text blocking translations | locale-file key parity test; every screen changed text on switch | PASS |
| Server error messages in both languages | BL006-1, BL006-3 (live backend, both languages, follows the UI switch) | PASS |

## Results by case
| ID | Case | Result |
|---|---|---|
| SETUP-1 | migrate on empty DB | PASS |
| BL007-1 | create_admin creates admin, no password in output | PASS |
| BL007-2 | create_admin twice is idempotent | PASS |
| BL007-3 | weak password rejected | PASS |
| BL007-4 | no password, no TTY: clean failure | PASS |
| BL007-5 | seed_demo creates all five roles | PASS |
| BL007-6 | seed_demo twice: counts 6 → 6 | PASS |
| BL007-7 | seed_demo refuses with DEBUG=False | PASS |
| BL007-8 | seed_demo without DEMO_PASSWORD fails cleanly | PASS |
| BL007-9 | seed_demo does not print password | PASS |
| BL001-1/2 | health 200 via header / query password | PASS |
| BL001-3 | health 403 missing and wrong password, identical bodies | PASS |
| BL001-4 | readiness 200, database ok | PASS |
| BL001-5 | health password never echoed | PASS |
| BL001-6 | POST health → 405 envelope | PASS |
| BL001-7 | unknown route, DEBUG=False → 404 envelope | PASS |
| BL001-7a | unknown route, DEBUG=True → Django HTML debug page (standard Django behaviour in dev; informational) | PASS |
| BL001-8/9/10/11 | Arabic messages (200, 403, 404), Content-Language, fallback to English | PASS |
| BL001-12/13 | docs, redoc, schema reachable; schema lists health + auth | PASS |
| BL001-14 | no hard-coded secrets in non-test backend source | PASS |
| BL001-16 | docs stay on outside production | PASS |
| BL001-17 | production settings: docs off, DEBUG off | PASS |
| AUTH-1/2/3 | login by username, phone, seeded user | PASS |
| AUTH-4 | wrong password and unknown user: 401, identical body | PASS |
| AUTH-5 | missing field → 400 with field error | PASS |
| AUTH-6/7 | refresh ok; bad refresh → 401 envelope | PASS |
| AUTH-8/9 | 401 in Arabic; no secret leakage | PASS |
| ADMIN-1 | /admin/login/ renders with Jazzmin | PASS |
| RATE-1 | health throttle 429 at the 121st request/min | PASS |
| RATE-2/3 | 429 envelope, Retry-After, Arabic | PASS |
| RATE-4 | auth throttle: 11th request in a minute → 429 | PASS |

### Frontend cases (real Chrome, real backend, 360px and 1280px)
| ID | Case | Result |
|---|---|---|
| BL002-1 | dev server renders home with title and Healthy | PASS |
| BL002-2 | home links to the four areas | PASS |
| BL002-3 | each area has its own layout | PASS |
| BL002-4 | unknown route → 404 page | PASS |
| BL002-5 | health request uses `VITE_API_URL` base | PASS |
| BL002-6 | backend down → friendly error with Retry | PASS |
| BL002-7 | backend back → Healthy | PASS |
| BL006-1 | network failure message localized (ar) | PASS |
| BL006-2 | 12 route × viewport combos: switch flips text + dir, persists after reload, no horizontal overflow | PASS (12/12) |
| BL006-3 | server 403 message English/Arabic follows UI language, refetched on switch | PASS |
| A11Y-1 | Tab order: skip link, switcher, area links, bottom nav; visible focus on each | PASS |
| A11Y-2 | landmarks, one main, labelled navs, one h1, `<html lang>` | PASS |
| A11Y-3 | touch targets ≥ 44px | PASS |
| BL005-1 | service worker activates (production build, localhost) | PASS |
| BL005-2 | Chrome installability errors: none | PASS |
| BL005-3 | manifest name, standalone, 192/512/maskable icons | PASS |
| BL005-4 | icons load (200) | PASS |
| BL005-5 | cache holds app shell only (11 entries), no `/api/` | PASS |
| BL005-6 | app shell opens offline | PASS |

Covered by automated tests only (not reproducible on a live server): 500 envelope without internals (`common/tests/test_exception_handler.py`), readiness failure with DB down (mocked), soft-delete behaviour.

## Task results
| Task | Item | Result | Notes |
|------|------|--------|-------|
| TASK-001 | BL-001 | PASS (backend) | Contract matched live behaviour in every case. Frontend confirmation still pending (TASK-022). |
| TASK-002 | BL-001 | PASS | Clean-checkout README flow works. |
| TASK-003 | BL-001 | PASS | Envelope + throttle verified live. Assignee left some acceptance boxes unticked; behaviour is correct. |
| TASK-004 | BL-001 | PASS | |
| TASK-005 | BL-001 | PASS | Login by username and phone. |
| TASK-006 | BL-007 | PASS | Assignee left acceptance boxes unticked; behaviour verified. |
| TASK-007 | BL-007 | PASS | Users only (by design). |
| TASK-008 | BL-001 | PASS | |
| TASK-009 | BL-006 | PASS | |
| TASK-010 | BL-002 | PASS | |
| TASK-011 | BL-002 | PASS | Health token flagged for Security (N-5). |
| TASK-012 | BL-006 | PASS | |
| TASK-013 | BL-006 | PASS | Verified against the live backend in both languages. |
| TASK-014 | BL-005 | PASS with gaps | Lighthouse has no PWA category any more; Chrome's installability check used instead. Real install / standalone launch not done (N-6). Icons are placeholders. |
| TASK-015 | BL-005 | PASS | |

## Bugs
### BUG-001: Placeholder secrets from `.env.example` are accepted in staging/production
- **Severity:** Low
- **Task:** TASK-002 (settings), TASK-004 (health password)
- **Steps to reproduce:** 1. `cp .env.example .env`. 2. Start with `config.settings.production` or `staging` and `SECRET_KEY=change-me`, `HEALTH_CHECK_PASSWORD=change-me`. 3. It starts; the 9-byte key also triggers PyJWT's `InsecureKeyLengthWarning` when issuing tokens.
- **Expected:** production/staging refuse to start with placeholder or too-short (<32) secrets.
- **Actual:** starts and signs JWTs with the placeholder.
- **Status:** VERIFIED (fixed in TASK-026: production and staging refuse placeholder or short secrets; retested 2026-10-10 by importing the production settings with `change-me`, a short key and an empty key (all refuse) and with a real key (starts)).

## Notes (not bugs)
- **N-1:** the project directory is not a git repository, so "no secrets committed" was checked by searching the tree, not `git grep`. `.gitignore` files exist for `.env`. Re-check once the repo exists.
- **N-2:** local venv is Python 3.12, Docker images use 3.13; no problem seen, but CI should pin one.
- **N-3:** `make test` runs pytest twice (full run + rate-limit subset), about 3 minutes.
- **N-5 (RESOLVED 2026-10-10, PO decision):** production health is checked from the server side (curl, tests, monitoring such as Sentry), not from the browser. The home-page health widget is now shown only in development (`import.meta.env.DEV`). Verified on the production build in Chrome: no widget, 0 health requests, and the health header name is not in the bundle. Unit tests: 49 passing.
- **N-6:** real "Add to home screen" and standalone launch need a headed Chrome or a phone; not done here. Please do a 2-minute manual check on a phone or desktop Chrome (install, open standalone).
- **N-7:** Playwright is not set up; `tests/e2e` is empty. The browser checks live in `qa/frontend_browser.mjs` (needs `puppeteer-core` and Chrome).
- **N-4:** the health password is browser-visible in the frontend dev build (already on the Security list, docs/TODO.md).

## Docker run (TASK-016/017/018/023), 2026-10-10
The PO allowed Docker to be run once. Run on Docker 29.8 / Compose 5.6 with a `.env` copied from `.env.example` and edited as the README says. Everything was torn down afterwards (containers, volumes, `.env` removed).

| Case | Result |
|---|---|
| `docker compose config` validates (local and staging) | PASS |
| One command (`docker compose up -d --build`, about 3m40s first time) starts db, backend, frontend in order (db healthy → backend healthy → frontend) | PASS |
| Backend container: migrates on start, runs as non-root `app`, healthcheck healthy, `/health/` and `/health/ready/` 200 | PASS |
| Frontend in real Chrome through the stack shows **Healthy**; CORS, language switch (ar/RTL) work | PASS (after BUG-002 fix) |
| Create admin (`make docker-create-admin`), seed demo (`make docker-seed`), login by API, admin page loads | PASS |
| `docker compose down` then `up` (volumes kept): same 6 users, login still works | PASS |
| `make docker-test`: backend 149 passed (1 skipped), frontend 47 passed, inside containers | PASS (after BUG-003 fix) |
| Images contain no `.env`, secrets, sqlite or venv; non-root users (`app`, `node`) | PASS |
| Staging stack (db, redis, backend, celery-worker, celery-beat) builds and runs; `/health/ready/` returns `database ok, redis ok, celery ok`; production-style settings in effect (DEBUG False, NUM_PROXIES 1, HTML accept → 406) | PASS (after BUG-004 fix) |
| CI pipeline cases (BL-004) | NOT RUN: CI deferred (TASK-019/020) |
| Fresh clone → running by the README alone | MOSTLY: followed the README; one wrinkle (admin/demo variables must be set before `docker compose up -d backend` so the container sees them) is documented |

### Bugs found by running Docker (all fixed and verified)
- **BUG-002 (High): frontend dev server broken in compose.** Named volume over `node_modules` was root-owned, so Vite (user `node`) got `EACCES` writing its cache and the page never rendered. Fix: Dockerfile now installs dependencies as `node`. Verified: Healthy in Chrome, no EACCES. Status: VERIFIED.
- **BUG-003 (Low): `make docker-test` failed at collection.** The compose-file tests read repo-root files that do not exist inside the backend container. Fix: the module skips itself when the root is not available. Status: VERIFIED.
- **BUG-004 (Medium): `celery-beat` crash-looped in staging.** It wrote `celerybeat-schedule` into `/app`, which the non-root user cannot write. Fix: `-s /tmp/celerybeat-schedule`. Status: VERIFIED (beat "Starting…", container stays up).
- **BUG-005 (Low): confusing compose warning** when `POSTGRES_PASSWORD` is unset. Fix: required-variable check in the backend DATABASE_URL. Status: VERIFIED.

### Notes from the run
- **N-8:** staging uses production settings, so API docs are off there (404) even though the contract lists docs as "development/staging". Set `API_DOCS_ENABLED=True` in the staging env if wanted. Needs a PO decision.
- **N-9:** the dev frontend logs one 404 in the browser console (a missing favicon). Cosmetic.
- **N-10:** the redis/celery readiness checks from docs/TODO.md are now verified against real Redis/Celery containers.
- Still not verified: CI behaviour, a real phone/desktop PWA install, `NUM_PROXIES=1` behind a real Nginx.

## Strict README run (E3, QA part), 2026-10-10
Clean copy of the repo (no `.env`, `node_modules`, venv or docs) in a new directory and compose project; README followed step by step, only editing `.env` as written, no pre-set variables this time.

| Step | Result |
|---|---|
| 1 `cp .env.example .env`, set 3 values | PASS |
| 2 `docker compose up --build` | PASS; first build took several minutes (slow download); the command stays in the foreground |
| 3 set admin/demo variables, `docker compose up -d backend`, `make docker-create-admin`, `make docker-seed` | PASS |
| 4 frontend shows Healthy; health 200; docs 200; admin login page | PASS |
| Log in at `/admin/` with the admin created in step 3 | **FAIL, then fixed** (BUG-006) |
| `docker compose down` then `up`: data persists, login still works | PASS |
| Torn down with `down -v`, scratch copy deleted | done |

- **BUG-006 (Medium): admin login landed on a 404 page.** Logging in through the real `/admin/login/` form redirected to `/accounts/profile/` (does not exist) because the Jazzmin form sends no `next` and Django's default login redirect was used. Earlier tests always sent `next=/admin/`, so they missed it. Fix: `LOGIN_URL` and `LOGIN_REDIRECT_URL` point to the admin; regression test added; re-checked in Chrome through the stack (lands on "Site administration"). Status: VERIFIED.
- **README gaps found and fixed:** `make` was called optional but step 3 used it (plain `docker compose exec …` commands added); step 2 did not say the command keeps running or that the first build is slow, nor to use a second terminal; the admin login credentials were not named in step 4.
- **E3 status:** QA's literal run passes. QA already knows the project, so a person who has never seen it should still do the check in `MANUAL_CHECKS.md`; this run reduces the risk of surprises.

## Deeper pass: API edge cases and accessibility (2026-10-11, no Docker)
Run with the venv server and the Vite dev server only (Docker is off limits per PO).

**API edge cases: 31/31 PASS** (`qa/api_edge_cases.py`, server with DEBUG=False, throttle relaxed). Unicode username, case-sensitive username, trimmed identifier, phone login, phone with spaces (401), soft-deleted user (401), password with trailing space, empty/null/number/list/dict values (400, never 500), malformed JSON (400 envelope), empty body, form-encoded body, wrong content type (415 envelope), a 1 MB password (401, no crash), 405 on GET/PUT/DELETE, CORS preflight, access token as refresh (401), valid and empty refresh, odd health tokens (NUL, 8 KB, unicode), odd `Accept-Language` values, quality values, deep unknown `/api/` paths (envelope).

**Accessibility: axe-core, 0 violations** (`qa/frontend_axe.mjs`): WCAG 2.0/2.1 A and AA plus best practices, on `/`, the four areas and the 404 page, in English and Arabic, at 360px and 1280px (24 combinations), including colour contrast. The Arabic font is loaded in every Arabic run and no text is clipped.

**New observation:** **N-11 (Low):** malformed JSON returns the generic message "Validation failed." with empty `errors`; the more precise "Malformed request." text exists in the exception handler but is never reached because 400 is matched first. Harmless; clients key on the status. Cosmetic fix for a later sprint.

## Clean-copy frontend check without Docker (2026-10-11)
README steps on a clean copy (no `node_modules`, no `dist`): `cp .env.example .env`, `npm ci` (6 s), `npm test` 49/49, `npm run lint` clean, `npm run build` OK (PWA: service worker, manifest, 15 precached files). PASS. Together with the clean-venv backend run this covers the no-Docker setup path.

## Regression after security fixes (2026-10-10)
TASK-024, TASK-025 and TASK-026 changed backend behaviour. Full backend suite: **159 passing, coverage 96%**, ruff clean. Live retests of the fixes are in `SECURITY_REPORT.md`. Login by username/phone, refresh, rate limits (auth 10/min, health 120/min), seeds and Arabic messages were re-covered by the suite. The frontend was not affected by these changes. Result: PASS.
