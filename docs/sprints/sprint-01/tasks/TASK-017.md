# TASK-017: Frontend Dockerfile for local development

- **Backlog item:** BL-003
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-010
- **Estimate:** S

## Description
Containerize the frontend dev server.

## Technical Notes
- `frontend/Dockerfile` (node LTS, `npm ci`, Vite dev server bound to `0.0.0.0` on 5173 with HMR). `.dockerignore` excludes `node_modules`, `.env`.
- Inside containers the API URL is provided by compose env (`VITE_API_URL`); note that the browser calls the backend via the host-published port, so document the difference between the browser URL and the container-to-container URL.
- Optional multi-stage production target (build + static serve); production deployment itself is out of scope for Sprint 01.

## Acceptance Criteria
- [x] `docker build` succeeds; dev server reachable on the published port (verified by a real run 2026-10-10 after fixing BUG-002)
- [x] No `.env` in the image
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — frontend: Wrote frontend/Dockerfile (node:22-slim, npm ci, non-root, Vite on 0.0.0.0:5173), .dockerignore, optional VITE_USE_POLLING for HMR on bind mounts, README section on browser vs container API URL. Production stage skipped (optional, out of Sprint 01 scope). Docker NOT built/run (PO decision), so the build criterion stays unchecked; files checked by 4 tests (47 total passing), lint clean, npm build OK. Status IN_REVIEW.
- 2026-10-10 — qa: PO lifted the no-Docker rule for one run. Executed for real (see QA_REPORT.md, section Docker run). BUG-002 found and fixed (node_modules volume owned by root, Vite could not write its cache, page did not render). After the fix Dockerfile builds and the dev server serves the app; frontend tests pass inside the container (47/47). Status DONE.
