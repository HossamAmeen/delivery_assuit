# TASK-022: QA test plan and execution: frontend skeleton, i18n, PWA

- **Backlog item:** BL-002
- **Assignee:** qa
- **Status:** DONE
- **Depends on:** TASK-010, TASK-011, TASK-013, TASK-015
- **Estimate:** M

## Description
Verify BL-002, BL-005 and BL-006 acceptance criteria in a real browser and with mobile emulation.

## Technical Notes
- Cases: home renders; the four area routes are separated; health call success and failure; `npm test` passes; language switch (ar RTL / en LTR) on all screens, persists after refresh, no overflow; server error message language follows UI; PWA installable (Lighthouse), standalone launch, icon/name, service worker does not cache `/api/`; layout at 360px and desktop; keyboard navigation basics.
- Optionally add Playwright smoke test `tests/e2e/smoke.spec.js` (home + language switch) to `tests/e2e` if Frontend scaffolding allows; coordinate via the Team Leader.
- Record in `QA_REPORT.md`; file BUG-XXX for failures.

## Acceptance Criteria
- [x] Test plan with traceability to BL-002/BL-005/BL-006 criteria
- [x] All cases executed with PASS/FAIL
- [x] BUG-XXX filed for failures

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — qa: Plan + execution in QA_REPORT.md. 30/30 browser cases PASS using puppeteer-core (not Playwright), Chrome installability check instead of Lighthouse. Not verified: real install and standalone launch (N-6). No bugs filed; observations N-5..N-7. No code changed.
