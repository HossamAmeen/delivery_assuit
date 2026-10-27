# TASK-016: Backend Dockerfile, entrypoint and DB wait script (local)

- **Backlog item:** BL-003
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-002
- **Estimate:** M

## Description
Containerize the backend for local development (skill sections 41-44).

## Technical Notes
- `backend/docker/local/Dockerfile` (python 3.13-slim, non-root user, deps from `requirements/development.txt`). `scripts/entrypoint.sh` (wait for DB, migrate, then run server) and `scripts/wait_for_db.sh` using `set -euo pipefail`.
- No secrets baked into the image; configuration only from env. `.dockerignore` excludes `.env`, db files and caches.
- Container healthcheck calls the health endpoint using the token from env, without printing it.

## Acceptance Criteria
- [x] `docker build` succeeds and the container serves the health endpoint when given a DB URL (verified by a real run 2026-10-10)
- [x] Image contains no `.env` or secrets (by inspection: .dockerignore + test; image not built)
- [x] Validated with the commands in the drf-backend skill section 57 (verified by a real run 2026-10-10: build, healthcheck healthy, migrate on start)
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — backend: Wrote backend/docker/local/Dockerfile (python 3.13-slim, non-root, healthcheck), .dockerignore, scripts/{entrypoint.sh,wait_for_db.sh,db_ready.py,healthcheck.py}; added psycopg[binary] to requirements/development.txt. Per PO decision Docker was NOT built or run, so the build/serve and skill-section-57 criteria stay unchecked. 17 new tests (scripts run for real: sqlite ok, unreachable DB times out without leaking the URL; Dockerfile/.dockerignore inspected); full backend suite 110 passing at last run, ruff clean. Status IN_REVIEW (pending a real docker build on the TODO list).
- 2026-10-10 — qa: PO lifted the no-Docker rule for one run. Executed for real (see QA_REPORT.md, section Docker run). Backend image built, container healthy, health + ready 200, runs as non-root `app`, no .env in image. Status DONE.
