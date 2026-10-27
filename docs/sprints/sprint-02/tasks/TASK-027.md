# TASK-027: Sprint 02 API contract: accounts, registration, login, logout

- **Backlog item:** BL-008..BL-013
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-026
- **Estimate:** S

## Description
Write `sprint-02/API_CONTRACT.md` first so Frontend can start in parallel. Same conventions as Sprint 01 (envelope, `/api/v1/`, Accept-Language, throttling).

## Technical Notes
- Endpoints: `POST /auth/register/driver/`, `/auth/register/trader/`, `/auth/register/client/`; `POST /auth/token/` (login, changed); `POST /auth/token/refresh/` (changed: rotation); `POST /auth/logout/`; `GET /auth/me/`.
- Document request/response/error examples, status values (`pending_approval`, `active`, `deactivated`), error `code` values for login (`account_pending`, `account_deactivated`) and the role-to-home mapping (driver: My Assigned Orders; trader: Dashboard; client: Home; admin/manager: Dashboard).
- State the token approach: access token short-lived (kept in memory by the frontend), refresh token rotated on every refresh and blacklisted on logout (also closes Sprint 01 note VULN-009).
- Define the permission matrix for BL-008 (who may call what; Manager cannot create/edit/delete Admin accounts).
- Mark clearly what changed vs Sprint 01 (login response now includes the user summary; refresh now returns a new `refresh`). Record a Change Log.

## Acceptance Criteria
- [x] Every endpoint above has request, success and error examples
- [ ] Frontend and QA confirm they can work from the contract alone
- [ ] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-11 — backend: Wrote API_CONTRACT.md (register x3, login changes + codes, rotating refresh, logout without bearer so it works after access expiry, /auth/me/, permission matrix, throttling, phone and password rules, change log). Decisions to confirm: (1) logout authenticated by the refresh token only; (2) new optional top-level `code` field on 403 account errors; (3) access token default lifetime 15 min; (4) phone normalised to digits, 8-15. Waiting for Frontend and QA to confirm they can work from it. Status IN_REVIEW.
- 2026-10-12 — PO approved decisions 1-4. Status DONE.
