# TASK-039: QA test plan and execution: backend accounts (BL-008..BL-013)

- **Backlog item:** BL-008..BL-013
- **Assignee:** qa
- **Status:** DONE
- **Depends on:** TASK-030, TASK-031, TASK-032, TASK-033
- **Estimate:** M

## Description
Verify the backend against the contract and acceptance criteria. QA does not fix code.

## Technical Notes
- Cases: every role allowed/denied; Manager vs Admin accounts; registration validation, duplicate phone, weak password, mass assignment (role/status in body ignored); login by phone/username, pending/deactivated, enumeration (body and timing), rate limits incl. spoofed `X-Forwarded-For`; refresh rotation, reuse, logout, deactivated refresh; Arabic messages; seed_demo twice.
- Run on a live server (venv, no Docker) with the black-box scripts extended; suite and coverage >= 80%. Record in `QA_REPORT.md`; file BUG-XXX.

## Acceptance Criteria
- [x] Test plan with traceability to BL-008..BL-013 backend criteria
- [x] All cases executed with PASS/FAIL
- [x] BUG-XXX filed for failures

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-16 — qa: Backend QA done (see QA_REPORT.md). Suite 291 passed, coverage 96%. Live black-box run 97/100 PASS (qa/accounts_blackbox.py). Filed BUG-007 (Medium): Arabic translations missing for the pending/deactivated login messages and the logout message. Status REJECTED; reassign BUG-007 to backend via Team Leader, retest needs only 3 cases plus the suite.
- 2026-10-16 — backend: BUG-007 fixed (Arabic for pending/deactivated login messages, logout message, and "Invalid token."; django.po + django.mo; 2 new Arabic tests). Suite 293 passed, ruff clean. Handed back to QA for retest; status left for QA.
- 2026-10-16 — qa: Retest of BUG-007 PASSED. BL012-9, BL012-9b, I18N-3 PASS on live server; full black-box 100/100; suite 293 passed, coverage 96%; Arabic "Invalid token." logout 400 verified. BUG-007 closed. Status DONE. TASK-040 not started.
