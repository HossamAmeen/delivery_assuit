# TASK-030: Registration endpoints for Driver, Trader and Client

- **Backlog item:** BL-009, BL-010, BL-011
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-028
- **Estimate:** M

## Description
Three public registration endpoints sharing one service.

## Technical Notes
- `POST /auth/register/driver/` `{full_name, phone, password, email?}`; `/trader/` `{full_name (shop/trader name), phone, password, email?}`; `/client/` `{full_name, phone, password, email?}`. Role and status are set by the server, never by the request.
- Validation: required fields with clear field errors; phone unique (normalised) with a clear message; password through Django's validators (weak -> field error); email optional, valid format and unique when given.
- Response 201 envelope with the user summary (no tokens: drivers/traders are pending; clients log in afterwards). Messages in Arabic and English.
- Throttle: scope `sensitive` plus a per-IP limit; spoofed `X-Forwarded-For` must not help (reuse `NUM_PROXIES`). Business logic in `services.py`.
- Registration reveals that a phone is already in use (required by the acceptance criteria); document this as an accepted enumeration surface and keep it rate-limited.

## Acceptance Criteria
- [x] Driver and Trader accounts are created `pending_approval`, Client `active`
- [x] Duplicate phone, weak password, missing fields return the 400 envelope with field errors
- [x] Role cannot be chosen by the client of the API (mass-assignment test)
- [x] Tests written and passing; coverage >= 80% on new code
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-12 — backend: Implemented. `UserManager.create_account()` (phone-only, username NULL), `services.register_account()` (transaction, IntegrityError -> clean phone 400), `RegisterSerializer` (input has no role/status; `is_valid_phone`, phone/email uniqueness, Django password validators with similarity attributes extended to full_name/phone in `AUTH_PASSWORD_VALIDATORS`), `RegisteredUserSerializer` (output), 3 views (`authentication_classes=[]`, `SensitiveRateThrottle`, per-IP, honours NUM_PROXIES), URLs `register/{driver,trader,client}/`, Arabic messages in `locale/ar` (+ compiled .mo). Duplicate phone also covers soft-deleted accounts (DB unique constraint). Tests: `apps/users/tests/test_register.py`. No migrations. Duplicate-phone message is the accepted enumeration surface per contract. Status -> IN_REVIEW.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results" (backend, TASK-039 APPROVED 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
