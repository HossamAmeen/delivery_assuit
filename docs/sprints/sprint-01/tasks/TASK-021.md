# TASK-021: QA test plan and execution: backend skeleton, health, auth, seed data

- **Backlog item:** BL-001
- **Assignee:** qa
- **Status:** DONE
- **Depends on:** TASK-004, TASK-007, TASK-008, TASK-009
- **Estimate:** M

## Description
Verify BL-001 and BL-007 against the API contract and acceptance criteria; also covers BL-007.

## Technical Notes
- Cases: health valid/invalid/missing password and no secret leakage; envelope on 400/401/403/404/429/500; Arabic vs English messages; JWT login by username and phone; rate limits (auth 10/min); /api/docs reachable in dev; create_admin works and is idempotent; seed_demo twice = no duplicates; no secrets in the repo (`git grep`/inspection); README steps reproducible.
- Run `pytest --cov` and confirm >= 80% coverage.
- Report defects as BUG-XXX in `QA_REPORT.md`; do not fix code.

## Acceptance Criteria
- [x] Test plan with traceability to BL-001/BL-007 acceptance criteria written in QA_REPORT.md
- [x] All cases executed; result PASS/FAIL recorded per case
- [x] Any BUG-XXX filed with steps to reproduce

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — qa: Test plan + execution in QA_REPORT.md: 42/42 live black-box cases PASS, suite 121 pass, coverage 92%, README followed in a clean directory. BUG-001 (Low) filed. Script: qa/backend_blackbox.py. No code was changed.
