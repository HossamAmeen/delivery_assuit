# TASK-138: Audit log screen

- **Backlog item:** BL-069
- **Assignee:** frontend
- **Status:** IN_REVIEW
- **Depends on:** TASK-134
- **Estimate:** S

## Description
Route `/admin/audit` listing the log with an action filter.

## Technical Notes
- See API_CONTRACT.md.

## Acceptance Criteria
- [x] Tests written and passing

## Activity Log
- 2026-10-27 — team_leader: Task created.
- 2026-10-27 — frontend: Built /admin/audit (AuditView): when, who, action label (unknown actions shown as they are), target, detail; action filter, paging, empty/error retry; read only; admin nav link. i18n keys use underscores because dots are read as paths. en and ar. 6 tests; Vitest 587 passed, eslint clean, vite build ok. Status IN_REVIEW. Not QA-tested (QA paused by PO until staging upload).
