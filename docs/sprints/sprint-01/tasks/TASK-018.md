# TASK-018: docker-compose stack, env example, DB volume and root README

- **Backlog item:** BL-003
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-016, TASK-017, TASK-004
- **Estimate:** M

## Description
Wire backend, frontend and database together so one command starts the system (BL-003). Compose lives at `backend/docker/local/docker-compose.yml` per the skill, or a root `docker-compose.yml` that includes it; the Team Leader prefers a root-level `docker-compose.yml` for a one-command start (`docker compose up`). Backend agent owns the file; frontend service only references the frontend Dockerfile (no Vue file edits).

## Technical Notes
- Services: `db` (PostgreSQL with a named volume), `backend`, `frontend`. Redis/Celery are not started (disabled). Backend depends on a healthy DB; frontend on backend.
- Root `.env.example` (no real secrets) covering compose, backend and frontend variables; README documents each variable. Real `.env` git-ignored.
- Make targets: `make docker-local` (up), plus down/logs helpers.
- Root README: prerequisites, fresh-clone steps (copy env, `docker compose up`, create admin via TASK-006 command, open URLs), how to run tests in containers.
- Docker is NOT run by agents (PO decision 2026-10-08): write the files only; no `docker build/up/compose config`.

## Acceptance Criteria
- [x] A single command starts backend, frontend and DB together  (verified 2026-10-10)
- [x] The frontend home page shows Healthy using the backend inside the compose network (verified 2026-10-10)
- [x] Stop and restart containers: data in the database persists (verified 2026-10-10)
- [ ] A fresh clone can be running by following the README only (QA verifies)
- [x] Docker files written (not executed); reviewed by reading
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-08 — team_leader: Scope add: also write docker/staging compose (backend, postgres, redis, celery-worker, celery-beat) — not run. Staging settings already exist (TASK-002).
- 2026-10-10 — backend: Wrote root docker-compose.yml (db with named volume, backend, frontend; healthcheck-ordered), .env.example, .gitignore, Makefile (docker-local/down/logs/test/create-admin/seed/reset), root README, staging scope add (backend/docker/staging/Dockerfile, docker/staging/docker-compose.yml with redis, celery-worker, celery-beat; RUN_MIGRATIONS=false switch in entrypoint.sh). Nothing was built or run (PO decision), so the runtime criteria stay unchecked; QA/PO must verify with a real docker compose up. 10 static tests (YAML parsed) + full backend suite passing, ruff clean. Status IN_REVIEW.
- 2026-10-10 — qa: PO lifted the no-Docker rule for one run. Executed for real (see QA_REPORT.md, section Docker run). Local stack: one command starts db+backend+frontend; browser shows Healthy via host port; admin and demo users survive down/up (volume kept); tests pass in containers (149 backend + 47 frontend). Staging stack (db, redis, backend, worker, beat) also run: /health/ready/ reports database, redis, celery ok. Bugs BUG-002..005 fixed. The README-only fresh start is still for a person to confirm (QA followed it with one deviation: pre-set admin/demo variables). Status DONE.
