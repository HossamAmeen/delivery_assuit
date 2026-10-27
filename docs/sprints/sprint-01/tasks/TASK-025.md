# TASK-025: Fix VULN-002 and VULN-003: login timing enumeration and admin brute force

- **Backlog item:** BL-001 (security fix)
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-024
- **Estimate:** M

## Description
VULN-002 (Medium): unknown identifiers answer in about 5 ms, existing accounts in about 800 ms. VULN-003 (Medium): `/admin/login/` has no throttling or lockout.

## Technical Notes
- VULN-002: when no user matches, run a dummy `check_password` against a fixed hash so timings are equal.
- VULN-003: throttle/lock out admin login (django-axes or small middleware using the shared cache); decide with the Team Leader. Keep Docker/CI unaffected.
- Tests for both; Security re-tests timing and 40-attempt admin run.

## Acceptance Criteria
- [x] Median login time for unknown vs existing user within noise (same order of magnitude)
- [x] Repeated bad admin logins are blocked or throttled
- [x] Tests written and passing; ruff clean

## Activity Log
- 2026-10-10 — team_leader: Task created from SECURITY_REPORT.md (VULN-002, VULN-003).
- 2026-10-10 — backend: VULN-002: authenticate_user always computes a hash (dummy hash for unknown users; inactive users no longer short-circuit). Live: existing 854 ms vs unknown 834 ms (was 833 vs 5). VULN-003: common/middleware.py AdminLoginThrottleMiddleware (5/IP, 30/username per 900 s, env-configurable, honours NUM_PROXIES, 429 + Retry-After, Arabic message, success clears counters). Live: attempts 1-5 processed, 6th+ 429, correct password refused while locked. 13 new tests (incl. window expiry with a fake clock); full suite 140 passing (about 3.3 min, slow because of PBKDF2 hashing; a fast test hasher would help), ruff clean, no migrations. Trade-off: per-username cap can lock out a real admin for the window. Awaiting Security retest. Status IN_REVIEW.
- 2026-10-10 — security/qa: retested live, VERIFIED (SECURITY_REPORT.md Retest). Full suite 159 passing, coverage 96%. Status DONE.
