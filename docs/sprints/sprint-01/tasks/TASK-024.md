# TASK-024: Fix VULN-001: throttle bypass via forged X-Forwarded-For

- **Backlog item:** BL-001 (security fix)
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** —
- **Estimate:** S

## Description
Security finding VULN-001 (High): DRF trusts the client-supplied `X-Forwarded-For` header when `NUM_PROXIES` is unset, so rotating the header gives a new throttle bucket per request and defeats the auth and health limits.

## Technical Notes
- Add `NUM_PROXIES` to `REST_FRAMEWORK`, read from env `NUM_PROXIES` (default `0` in base/development: use REMOTE_ADDR only; production/staging document `1` behind Nginx).
- Add the variable to `.env.example`, README, root `.env.example`/compose where relevant.
- Tests: with `NUM_PROXIES=0` a spoofed header must not create a new bucket (429 after the limit); with `NUM_PROXIES=1` the last hop is used.
- Security re-tests with 30 attempts and rotating `X-Forwarded-For`.

## Acceptance Criteria
- [x] 30 login attempts with rotating `X-Forwarded-For` are throttled (429 after 10 per minute)
- [x] `NUM_PROXIES` is env-configurable and documented
- [x] Tests written and passing; ruff clean

## Activity Log
- 2026-10-10 — team_leader: Task created from SECURITY_REPORT.md (VULN-001, High, blocks release).
- 2026-10-10 — backend: Added REST_FRAMEWORK NUM_PROXIES (env, default 0) in base.py; .env.example + README section; staging compose sets NUM_PROXIES (default 1, behind Nginx). 6 new tests in common/tests/test_throttle_proxies.py (verified they FAIL when NUM_PROXIES is unset, i.e. they catch the bug). Live re-run of the exploit: 30 attempts with rotating X-Forwarded-For -> 10x401 then 20x429. Full suite 127 passing, ruff clean. Needs Security retest to mark VULN-001 VERIFIED. Status IN_REVIEW.
- 2026-10-10 — security/qa: retested live, VERIFIED (SECURITY_REPORT.md Retest). Full suite 159 passing, coverage 96%. Status DONE.
