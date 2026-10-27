# Sprint 03

- **Goal:** Account management: users manage profile, password, and email recovery; Admin/Manager manage users and Manager accounts, activate/deactivate accounts, and approve driver and trader registrations; consistent validation and UI states.
- **Status:** IN_PROGRESS (all backend TASK-044..053 and frontend TASK-054..061 are built; TASK-044, TASK-045, TASK-054 DONE for QA; TASK-046..053 and TASK-055..061 IN_REVIEW; TASK-062 (loading/empty/error/offline states) IN_REVIEW; QA TASK-063/064 and Security paused by PO; VULN-012 awaits Security retest; BUG-010 Low open)
- **Approval to start:** APPROVED by the PO on 2026-10-26, together with acceptance of Sprint 02 exceptions E1–E4 (`../sprint-02/APPROVAL.md`)

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-014 | Change password | SEC-02 | Must | both |
| BL-015 | Profile view and edit (all roles) | SEC-02 | Must | both |
| BL-016 | Password recovery via email | SEC-02 | Should | both |
| BL-078 | Admin/Manager approves driver and trader registrations | SEC-08 | Must | both |
| BL-052 | Account activate/deactivate | SEC-08 | Must | both |
| BL-059 | Users overview and Admin/Manager account management | SEC-08 | Must | both |
| BL-064 | Input validation and clear error messages | SEC-10 | Must | both |
| BL-065 | Global error, loading, and empty states | SEC-10 | Should | frontend |

Order is dependency order, not the old backlog number order. BL-078 comes before BL-052 and BL-059 because approval is what turns a pending driver or trader into an account that can be activated. BL-059 depends on BL-052. BL-016 depends on BL-015 (a user must be able to add an email). BL-064 and BL-065 apply to the screens this sprint adds.

## Carry-over from previous sprint
Sprint 02 is approved with exceptions and is not deployed. These items move here. They are not new features.

### In this sprint
- **TASK-042 / VULN-012 (Medium, open).** PO decision 2026-10-17 deferred it here; accepted as E3 on 2026-10-26. **PO choice 2026-10-26: cookie.** The refresh token moves to an `HttpOnly; Secure; SameSite=Strict` cookie on the auth path. The access token stays in memory. Refresh and logout use that cookie plus an Origin check. Login, refresh, and logout change. CSP is not this fix. `localStorage` must stop holding the refresh token. See TASK-044, TASK-045, and TASK-054.
- **VULN-017 (Low) ships with BL-014 and BL-016.** Password change and password reset must revoke that user's refresh tokens. Reuse of an already-rotated refresh token must revoke that user's outstanding refresh tokens. This was required by the time recovery exists.
- **VULN-018, email half, ships with BL-015 and BL-016.** A non-empty email must be unique in the database after normalisation (lower case). Phone OTP is not a backlog item and is not added in this sprint. The reset API always returns the same 200 so it does not reveal whether the account exists. The screen always tells the user to contact an administrator if they have no email.
- **VULN-014, VULN-015, VULN-016, VULN-019 (Low) are one hardening batch in this sprint.** They were triaged to Sprint 03 and they sit on the auth endpoints this sprint extends: no 500 on deep or oversized JSON, login field length caps, stricter phone-versus-username normalisation, and `Cache-Control: no-store` on auth responses. Nginx `client_max_body_size` stays with DevOps (deploy is still deferred).
- **QA N-14.** When BL-059 exists, re-test the role matrix and Manager-versus-Admin rules on the live endpoints, not only the test URLconf.

### Accepted and still open, not built in this sprint
- **E1.** PostgreSQL run of the exactly-one-200 refresh test (VULN-011) and migration `0002_user_status`. Runs in CI or at the first staging deploy. CI itself is still deferred (TASK-019/020).
- **E2.** VULN-013 outside-the-host retest and the staging checks in Sprint 02 `APPROVAL.md`. Hard gate before any staging or production deploy. Not a Sprint 03 feature.
- **VULN-020 (Info).** Accepted. Dev servers stay off public networks.
- **VULN-021 (Info).** Optional. `seed_demo` must not be forced on staging or production. A settings-module refusal can wait for deploy work.
- **VULN-022 (Info).** Per-IP auth throttle stays. BL-016 already requires recovery to be rate-limited; a per-identifier limit can be part of that task if it stays small.
- **Sprint 01 leftovers.** Real-device PWA install check (last item in `docs/TODO.md`), CI (TASK-019/020), DevOps deploy files, brand/PWA icons. Still deferred. No local Docker (PO).

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] VULN-012 is closed by the HttpOnly refresh cookie, and VULN-017 is done with password change, reset, deactivation, and reuse detection
- [ ] Backend + QA signed APPROVAL.md
- [ ] No deploy. E2 is still the gate before staging or production

## Risks
- Manager must not create, edit, or delete Admin accounts (BR-14). BL-059 needs a dedicated permission test. Admin and Manager stay otherwise equal.
- Rejection is a new status, `rejected`, so it is not the same as `deactivated` (BL-052). TASK-049 adds it. Login with the right password returns `account_rejected` and no token.
- BL-052 says deactivating a driver who has an active order must not lose that order. Orders do not exist yet (Sprint 05). Record the rule. Do not build orders in this sprint. The "order stays assigned" check waits until orders exist.
- "Each change is recorded with who and when" on BL-052 and BL-078 means a minimal record on that action. The full audit trail is BL-069 in Sprint 10. Do not build BL-069 here.
- Email is optional at registration and required only for recovery (BL-016). Dev has no mailbox requirement: tests use Django's locmem backend, and local dev may use the console backend. A real SMTP server is deploy work.
- The cookie change reopens Sprint 02 login, refresh, and logout. Those three are retested in this sprint's QA pass.
- Eight product items plus the security carry-over is at the top of what one sprint should hold. If it slips, BL-065 (Should) is the first item to move out. Do not drop BL-014, BL-015, BL-078, BL-052, BL-059, or VULN-017.
- Username stays an optional unique profile field. Drivers still register with name, phone, and password only. Users still cannot change their own role or status.
- No local Docker. Tests use the venv and npm. QA uses live servers.

## Decision recorded (2026-10-26)
VULN-012: **cookie.** Details are in TASK-044. The Team Leader has written TASK-044..064. Backend starts at TASK-044 (the contract) and does not implement until that task is picked up.

## Tasks (TASK-044..064)
| Task | Assignee | Title |
|------|----------|-------|
| TASK-044 | backend | API contract (contract first, includes the cookie session) |
| TASK-045 | backend | Refresh cookie, Origin check, reuse detection (VULN-012, VULN-017) |
| TASK-046 | backend | Change password and revoke sessions (BL-014, VULN-017) |
| TASK-047 | backend | Profile edit and unique email (BL-015, VULN-018) |
| TASK-048 | backend | Password recovery (BL-016, VULN-017) |
| TASK-049 | backend | Approve or reject driver and trader (BL-078) |
| TASK-050 | backend | Activate and deactivate (BL-052, VULN-017) |
| TASK-051 | backend | Users list and detail (BL-059) |
| TASK-052 | backend | Create, edit, delete users (BL-059, BR-14) |
| TASK-053 | backend | Auth hardening (VULN-014, VULN-015, VULN-016, VULN-019) |
| TASK-054 | frontend | Cookie session; drop localStorage refresh (VULN-012) |
| TASK-055 | frontend | Change-password screen (BL-014) |
| TASK-056 | frontend | Profile screen (BL-015) |
| TASK-057 | frontend | Password recovery screens (BL-016) |
| TASK-058 | frontend | Approval queue and rejected login (BL-078) |
| TASK-059 | frontend | Users list, activate, deactivate (BL-052, BL-059) |
| TASK-060 | frontend | Create, edit, delete user screens (BL-059) |
| TASK-061 | frontend | Field validation on the new forms (BL-064) |
| TASK-062 | frontend | Loading, empty, error, offline states (BL-065) |
| TASK-063 | qa | Backend QA |
| TASK-064 | qa | Frontend QA |

Order: TASK-044 first. Backend 045 to 053 after the contract (045 before 046, 048, and 050, because those clear the cookie). Frontend 054 can start once TASK-044 is DONE; 055 to 060 follow 054; 061 and 062 after the screens exist. QA last. Then Security reviews the sprint.
