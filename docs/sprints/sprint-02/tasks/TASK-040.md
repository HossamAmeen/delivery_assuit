# TASK-040: QA test plan and execution: frontend accounts (BL-009..BL-013)

- **Backlog item:** BL-009..BL-013
- **Assignee:** qa
- **Status:** DONE
- **Depends on:** TASK-036, TASK-037, TASK-038, TASK-039
- **Estimate:** M

## Description
Verify screens in a real browser (headless Chrome) against the live backend; no Docker.

## Technical Notes
- Cases: register each role, login each role to the correct home, pending/deactivated messages, wrong password message, refresh keeps session, logout and back button, guard redirects, Arabic/RTL and 360px on every new screen, keyboard use, axe accessibility, token not in URL or logs.
- Record in `QA_REPORT.md`; file BUG-XXX.

## Acceptance Criteria
- [x] Test plan with traceability
- [x] All cases executed with PASS/FAIL
- [x] BUG-XXX filed for failures

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-16 — qa: Executed in headless Chrome against live backend (no Docker): 117/120 cases PASS, axe 0 violations (60 runs). Filed BUG-008 (Low, TASK-037: no focus move on pending screen) and BUG-009 (Medium, TASK-037/035: focused field hidden under fixed bottom nav). Scripts and outputs in docs/sprints/sprint-02/qa/. Status -> REJECTED; see QA_REPORT.md.
- 2026-10-16 — qa: Retest after fixes: BUG-008 and BUG-009 VERIFIED (incl. A11Y-F1 at 360x700, Tab to Confirm password). Browser 120/120 PASS, axe 60 runs 0 violations, no regressions (one transient BL009-10 failure was a QA-script preflight capture issue, fixed in the script). No Docker; all servers stopped. Status -> DONE; see QA_REPORT.md.
