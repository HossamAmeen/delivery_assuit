# TASK-037: Registration screens (Driver, Trader, Client)

- **Backlog item:** BL-009, BL-010, BL-011
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-034, TASK-035
- **Estimate:** M

## Description
One shared registration form component used by three routes.

## Technical Notes
- Routes `/register/driver`, `/register/trader`, `/register/client` plus a chooser page `/register`. Fields: name (label differs for Trader: shop/trader name), phone, password (+confirm), optional email. Show password rules; show server field errors (duplicate phone, weak password).
- After success: Client -> go to login with a success note (or auto-login if contract says so); Driver/Trader -> a clear 'pending approval' confirmation screen.
- Bilingual, accessible, 360px friendly.

## Acceptance Criteria
- [x] Missing fields and server errors are shown per field
- [x] Pending approval screen explains next steps
- [x] Component tests; lint clean; tests passing
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-15 — frontend: Implemented chooser + shared RegisterView (3 routes), pending-approval screen, client redirect to login with success note; 163 frontend tests pass, eslint clean. Status IN_REVIEW.
- 2026-10-16 — frontend: BUG-008 fix: RegisterView focuses the pending-screen `<h1>` (ref + nextTick) after success; BUG-009 fix via scroll-padding-bottom in main.css. Tests added in register.spec.js; suite 178/178, eslint clean. Status IN_REVIEW; ready for QA retest.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results (frontend)" (TASK-040 APPROVED, retest 120/120 on 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
