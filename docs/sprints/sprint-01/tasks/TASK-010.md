# TASK-010: Frontend Vue 3 skeleton: Vite, Pinia, router areas, lint and Vitest

- **Backlog item:** BL-002
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** —
- **Estimate:** M

## Description
Create `frontend/` with Vue 3 (Composition API, `<script setup>`), Vite, Pinia, Vue Router, ESLint + Prettier and Vitest.

## Technical Notes
- Structure per `agents/frontend.md`: `src/{api,components,views,stores,router,composables,utils,assets}`, `tests/{unit,e2e}`.
- Router with separated areas and empty placeholder layouts: `/driver/*`, `/trader/*`, `/client/*`, `/admin/*` (Admin/Manager). Home page `/` renders (title + links to the four areas). Add a 404 route. No feature screens, no auth guards yet (note: guards arrive with SEC-02).
- `.env.example` with `VITE_API_URL=http://localhost:8000/api/v1`. Scripts: `dev`, `build`, `test`, `lint`, `format`.
- One sample Vitest test (e.g., Home view renders) passing. README section: run frontend + tests. Do not use `v-html`.

## Acceptance Criteria
- [x] `npm run dev` renders the home page; each area route renders a distinct placeholder layout
- [x] `npm test` runs one command and passes
- [x] `npm run lint` clean; `npm run build` succeeds
- [x] README has frontend run + test instructions
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — frontend: Created frontend/ (Vue 3 script setup, Vite, Pinia, Vue Router, ESLint flat config + Prettier, Vitest). Home + 4 placeholder area layouts + 404, no guards. 6 tests passing; lint clean; build OK; dev server serves the app. frontend/README.md added; .env.example has VITE_API_URL. Status IN_REVIEW.
- 2026-10-10 — qa: TASK-022 frontend QA PASS (QA_REPORT.md; 30/30 real-browser cases, 47 unit tests); status DONE.
