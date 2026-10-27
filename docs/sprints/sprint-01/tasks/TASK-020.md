# TASK-020: CI pipeline: frontend lint, test and build job

- **Backlog item:** BL-004
- **Assignee:** frontend
- **Status:** DEFERRED
- **Depends on:** TASK-019, TASK-010
- **Estimate:** S

> **DEFERRED:** CI is deferred by PO (2026-10-08); tracked in docs/TODO.md. Do not implement in Sprint 01.

## Description
Add the frontend job to the existing pipeline file created in TASK-019 (Frontend edits only the frontend job section).

## Technical Notes
- Node LTS, `npm ci` with cache, `npm run lint`, `npm run format -- --check` (or prettier check), `npm test`, `npm run build`.
- Jobs run in parallel with the backend job; pipeline status is failure if either fails.

## Acceptance Criteria
- [ ] Frontend steps run green in CI configuration and fail visibly on a failing test or lint error
- [ ] Both jobs appear in the same pipeline run
- [ ] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
