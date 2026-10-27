# TASK-036: Login screen

- **Backlog item:** BL-012
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-034, TASK-035
- **Estimate:** M

## Description
Login form with phone-or-username identifier.

## Technical Notes
- Fields: identifier, password (show/hide). Client-side required validation; server field errors under the fields; generic invalid-credentials message; friendly pending-approval and deactivated messages (from `code`). Loading, error states; disabled while submitting; 429 message.
- After success go to the role home from the response's user summary. Link to registration. RTL/LTR and 360px layout, labels and keyboard support (Enter submits).

## Acceptance Criteria
- [x] Each acceptance criterion of BL-012 is visible in the UI
- [x] Arabic/English complete; no overflow at 360px
- [x] Component tests (valid, invalid, pending, deactivated, 429, network error)
- [x] Lint clean; tests passing
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-15 — frontend: Implemented LoginView (replaces placeholder on `login` route only; name/guestOnly meta kept), en/ar strings, 14 Vitest tests. Full suite 147/147 passing, eslint clean. Status -> IN_REVIEW.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results (frontend)" (TASK-040 APPROVED, retest 120/120 on 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
