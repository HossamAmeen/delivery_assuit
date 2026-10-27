# TASK-019: CI pipeline: backend lint and test job

- **Backlog item:** BL-004
- **Assignee:** backend
- **Status:** DEFERRED
- **Depends on:** TASK-002
- **Estimate:** S

> **DEFERRED:** CI is deferred by PO (2026-10-08); tracked in docs/TODO.md. Provider decided: GitHub Actions. Do not implement in Sprint 01.

## Description
Create the CI pipeline file with the backend job. CI provider is not specified in the backlog; the story says 'push/merge request' (GitLab wording). Default: GitHub Actions at `.github/workflows/ci.yml` unless the PO says GitLab (`.gitlab-ci.yml`). Flagged to PO in the sprint report.

## Technical Notes
- Triggers: every push and pull/merge request. Backend job: Python 3.13, cache pip, install `requirements/development.txt`, `ruff check .`, `ruff format --check .`, `python manage.py check`, `makemigrations --check --dry-run`, `pytest --cov=. --cov-fail-under=80`.
- Use test env variables defined in the workflow (dummy values, never real secrets). Failing step fails the pipeline.

## Acceptance Criteria
- [ ] Pipeline file validated (syntax) and runs the backend steps locally via the same commands
- [ ] A deliberately failing test (demonstrated in a branch/PR or dry run) turns the job red
- [ ] Lint failure also fails the job
- [ ] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
