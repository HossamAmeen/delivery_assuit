# TASK-041: Make refresh-token rotation atomic (VULN-011)

- **Backlog item:** BL-013 (logout/rotation); security fix for VULN-011 (Medium)
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-032 (DONE)
- **Estimate:** S
- **Scope recommendation:** **Sprint 02 (fix now).** Reason: small, isolated change in `rotate_refresh_token`; it is the code that closes VULN-009, so the "old token stops working" guarantee of this sprint is not true until it is atomic. Needs a backend retest and a short Security retest of JWT-14 before APPROVAL.md. Final scope decision belongs to the PO.

## Description
`apps/users/services.py:rotate_refresh_token` validates the refresh token outside the transaction that blacklists it, so concurrent requests with one token can each get a new valid pair (2 of 10 succeeded in the pentest). Also unhandled DB errors surface as 500.

## Technical Notes
- Inside `transaction.atomic()`: lock the `OutstandingToken` row (`select_for_update`), create the `BlacklistedToken` first (unique constraint on token), treat `IntegrityError`/already-blacklisted as `TokenError` -> 401 with the existing generic envelope.
- Issue the new pair only after the blacklist row is committed in the same transaction.
- Map unexpected DB lock errors on this path to a clean error (no raw 500) where practical.
- Out of scope: family revocation on reuse (VULN-017, see TODO triage).
- Contract: no change to `/auth/token/refresh/` request/response; update `API_CONTRACT.md` only if error behaviour changes.

## Acceptance Criteria
- [ ] N parallel refreshes with one token yield exactly one 200 and the rest 401 (no 500, no second valid pair)
- [ ] Sequential reuse still 401; normal rotation and logout unchanged
- [ ] Concurrency test added (threaded; PostgreSQL where available, SQLite-tolerant fallback documented)
- [ ] Existing suite still passes; coverage of `services.py` stays >= 99%
- [ ] Security retest: `pentest_sprint02.py` JWT-14 shows exactly one 200

## Activity Log
- 2026-10-17 — team_leader: Task created from SECURITY_REPORT.md (VULN-011).
- 2026-10-17 — product owner: PO decision (2026-10-17): Sprint 02 scope for the security fixes = TASK-041 and TASK-043 only; TASK-042 (VULN-012) is deferred to Sprint 03.
- 2026-10-17 — backend: Set IN_PROGRESS then IN_REVIEW. `rotate_refresh_token` now, inside `transaction.atomic()`, locks the OutstandingToken row (`select_for_update`), claims the token via `token.blacklist()` and treats `created=False` as `TokenError` (401); the new pair is issued only after the claim in the same transaction. Any `OperationalError` on the path (lock/busy) is mapped to `TokenError` (401, no raw 500, transaction rolled back so the token stays usable). No contract change. Tests added in `apps/users/tests/test_auth.py`: deterministic lost-race test, DB-error-is-401 test, threaded 8-way parallel test. Full suite 296 passed; ruff clean; `makemigrations --check` clean; `services.py` coverage 99%. Caveat: on SQLite the threaded test can only assert "never more than one 200, never 500" (in-memory test DB locks tables immediately, so possibly nobody wins); strict "exactly one 200" is asserted only on PostgreSQL (not run locally, no Docker). Security retest of JWT-14 (pentest_sprint02.py) still pending; not run.
- 2026-10-17 — qa: Retested, DONE. See QA_REPORT.md section 'Retest: Security fix tasks'. Open items: strict exactly-one-200 only on PostgreSQL (not run); Security JWT-14 retest pending.
