# Sprint 02 Approval

## Gate result: ACCEPTED BY THE PO — approved with exceptions, not deployed
All three required inputs exist (Backend, QA, Security). Backend and QA sign off, Security result is PASS. **PO acceptance: ACCEPTED on 2026-10-26.** The PO accepted E1, E2, E3, and E4 as written and approved Sprint 03 to start. Nothing from Sprint 02 is deployed in this step. E2 stays a hard gate before any staging or production deploy. E1 is checked when CI or the first staging PostgreSQL run happens. DevOps does not deploy until that gate is actually checked (`AGENTS.md`: no deploy without an approved `APPROVAL.md`, and E2 is part of this approval).

## Scope delivered
Goal: users register as Driver, Trader or Client, log in by phone or username, and log out, landing on a role-specific home screen.

| BL | Title | Tasks | Result |
|----|-------|-------|--------|
| BL-008 | User roles and role-based access | TASK-027, 028, 029, 035 | Delivered |
| BL-009 | Driver registration | TASK-030, 037 | Delivered |
| BL-010 | Trader/Shop registration | TASK-030, 037 | Delivered |
| BL-011 | Client registration | TASK-030, 037 | Delivered |
| BL-012 | Login (phone or username) | TASK-031, 034, 036, 038 | Delivered |
| BL-013 | Logout | TASK-032, 034, 038 | Delivered |
| BL-007 (follow-up) | seed_demo per role/status | TASK-033 | Delivered |

- QA tasks: TASK-039 (backend QA, DONE), TASK-040 (frontend QA, DONE).
- Security fix tasks in scope by PO decision 2026-10-17: TASK-041 (VULN-011, DONE) and TASK-043 (VULN-013, DONE).
- **Not delivered: TASK-042 (VULN-012, refresh token in `localStorage`, CSP / cookie design).** Status TODO, **deferred to Sprint 03 by PO decision 2026-10-17.**
- Bugs: BUG-007 (Medium), BUG-008 (Low), BUG-009 (Medium) all fixed and verified. No open bugs.

## Backend Sign-off
- **Status:** APPROVED, with the bookkeeping note in E4
- **Date:** 2026-10-17
- **Tests:** 296 backend tests passing (QA retest run `qa/retest_backend_suite.out`), coverage 96%, `services.py` 99%; ruff clean and `makemigrations --check` clean (per TASK-041 log). Frontend (developer-reported in TASK-037): 178 Vitest tests passing, eslint clean.
- **Migrations:** `apps/users/migrations/0002_user_status` (status field, nullable unique username, phone normalisation) plus the `token_blacklist` app migrations. Not run on PostgreSQL (QA N-15).
- **Notes:**
  - API contract (`API_CONTRACT.md`) approved by the PO 2026-10-12 and unchanged by the security fixes.
  - TASK-041 makes refresh rotation atomic (row lock plus claim by blacklisting, `OperationalError` mapped to 401). Strict "exactly one 200" is only asserted on PostgreSQL (E1).
  - Known limits: no user-management endpoint yet (role matrix covered by suite only); Drivers/Traders stay `pending_approval` until the Sprint 03 approval screen (demo uses seeded accounts); access tokens live up to 15 min after logout (documented).

## QA Sign-off
- **Status:** APPROVED, conditional on the PO accepting E1 to E4
- **Date:** 2026-10-17
- **Open bugs:** none. BUG-007, BUG-008, BUG-009 fixed and verified. No Critical/High.
- **Evidence (from `QA_REPORT.md`):**
  - Backend: suite 296 passed, coverage 96% (retest 2026-10-17; 293 on 2026-10-16); black-box against a live dev server 100/100 PASS; parallel-refresh live run 61 PASS, 0 FAIL (10 races, 150 requests, 0 x 500, exactly one 200 on SQLite).
  - Frontend: 120/120 real-browser cases PASS (headless Chrome, live backend); axe-core 60 runs, 0 violations.
  - No Docker run (PO rule); all QA servers stopped.
- **Not covered by QA:** PostgreSQL; production build / PWA service worker re-run (N-20); real-device PWA install (Sprint 01 E2 still open in `docs/TODO.md`); TASK-043 verified by review only (YAML parsed and files read, nothing executed).

## Security Result
- **Release decision: PASS** (`SECURITY_REPORT.md`, retest 2026-10-17). Critical 0, High 0.
- **VULN-011 (Medium): FIXED WITH CONDITIONS.** Fix verified by code review, JWT-14 (6 races, exactly one 200, 0 x 500) and a lock-error test on SQLite. Condition: PostgreSQL run (E1).
- **VULN-013 (Medium): FIXED WITH CONDITIONS.** Fix verified by review (loopback bind, `X-Forwarded-For $remote_addr` snippet, docs). Conditions: outside-the-host retest and staging checks (E2). This remains a hard gate before any staging/production deploy.
- **VULN-012 (Medium): OPEN, deferred to Sprint 03** by PO decision (TASK-042). No XSS sink exists today (no `v-html`, `innerHTML`, `eval`); the gap is the missing CSP and the localStorage refresh token.
- **VULN-014 to VULN-022 triage (no tasks, nothing blocks release):**

| Finding | Sev | Status | Suggested home |
|---------|-----|--------|----------------|
| VULN-014 500 on deep JSON / oversized body / odd claim | Low | OPEN | Sprint 03 hardening batch + Nginx `client_max_body_size` |
| VULN-015 login identifier/password unbounded length | Low | OPEN | Sprint 03 hardening batch |
| VULN-016 lenient identifier normalisation | Low | OPEN | Sprint 03 hardening batch |
| VULN-017 no reuse detection; sessions survive password change | Low | OPEN | Sprint 03 with password recovery (at the latest) |
| VULN-018 unverified phone/email, no DB-unique email | Low | OPEN | Sprint 03 (OTP/recovery) |
| VULN-019 token responses lack `Cache-Control: no-store` | Low | OPEN | Sprint 03 hardening batch |
| VULN-020 dev SECRET_KEY fallback | Info | Accepted | Keep dev servers off public networks |
| VULN-021 `seed_demo` superuser | Info | Open (optional) | Never `--force` on staging/production; optionally refuse by settings module |
| VULN-022 per-IP shared auth throttle | Info | Open | Revisit with per-identifier limits in Sprint 03 |

## Exceptions the PO must accept (or ask to be closed first)
- **E1: PostgreSQL concurrency run of the exactly-one-200 refresh test (VULN-011 / TASK-041).** Only SQLite was used (it serialises writers, so the result is not proof for PostgreSQL). Run the threaded test in `apps/users/tests/test_auth.py` and Security's JWT-14 against PostgreSQL (CI or first staging) before relying on the strict guarantee. QA also notes (N-21) that a loser hitting a DB lock gets 401, not 503. Same run should cover migration `0002_user_status` on PostgreSQL (QA N-15).
- **E2: VULN-013 outside-the-host retest and staging checks, at the first staging deploy (DevOps gate).** (a) THR-1/np1 from outside the host: forged `X-Forwarded-For` must reach 429 after the limit; (b) `ss -ltnp` shows port 8000 on 127.0.0.1 only; (c) firewall allows only 80/443; (d) the real Nginx config includes `docker/staging/nginx-proxy-headers.conf` (the repo has no full site template); (e) staging env has `NUM_PROXIES=1`; (f) a containerised Nginx uses `backend:8000` on the compose network. TASK-043 was verified by review only; nothing was run against a deployed topology.
- **E3: VULN-012 deferred to Sprint 03 (TASK-042 not delivered).** The refresh token stays in `localStorage` and there is no CSP until then. Accepting this means no public/production release should rely on it; interim CSP and the `vue/no-v-html` lint guard are also not done. The Low findings VULN-014 to VULN-019 stay open as listed above, with VULN-017 required by the time password recovery ships.
- **E4: Open items found in the reports and task files.**
  1. ~~Task status bookkeeping~~ **RESOLVED 2026-10-24 (Team Leader):** TASK-028..038 set to `DONE` in their task files (QA passed them, `QA_REPORT.md`). Only TASK-042 is not `DONE` (TODO, deferred to Sprint 03, see E3).
  2. Not re-run by QA: production build / PWA service worker (N-20) and the Sprint 01 real-device PWA install check (E2 of Sprint 01, last item in `docs/TODO.md`).
  3. Role matrix and Manager-vs-Admin rules are tested only through the test-only URLconf; re-test live when Sprint 03 adds user management (QA N-14).
  4. Brand/PWA icons, CI (TASK-019/020) and DevOps deploy files are still deferred (Sprint 01 carry-over).
  5. The frontend unit-test count (178) is developer-reported in the task logs; QA's report counts browser cases (120) and does not restate it.

## PO acceptance
- **Status:** ACCEPTED
- **Date:** 2026-10-26
- **Decision:** Accept E1, E2, E3, and E4 as written. Sprint 03 is approved to start. No deploy in this step.
- E1 stays open until the PostgreSQL exactly-one-200 refresh run (CI or first staging).
- E2 stays a hard gate: the outside-the-host VULN-013 checks must pass before any staging or production deploy.
- E3: TASK-042 / VULN-012 and the Low findings move with Sprint 03 as written in `docs/sprints/sprint-03/SPRINT.md`. No public or production release should rely on the localStorage refresh token.
- E4 stays as listed (item 1 already resolved on 2026-10-24). CI, deploy files, and the real-device PWA check stay deferred.
