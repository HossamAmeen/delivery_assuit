# TASK-011: Frontend API service (axios) and end-to-end health check call

- **Backlog item:** BL-002
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-010, TASK-004
- **Estimate:** M

## Description
Create the shared API layer and demonstrate it with one call to the backend health check on the home page.

## Technical Notes
- `src/api/http.js`: single axios instance, `baseURL = import.meta.env.VITE_API_URL`; request interceptor placeholder for JWT; response interceptor normalising the error envelope `{success:false, message, errors}`. `src/api/health.js` service; `src/stores/health.js` Pinia store; Home shows a status widget with loading, healthy, and error states.
- Health call sends header `X-Health-Check-Token` from `VITE_HEALTH_CHECK_TOKEN`. SECURITY NOTE: this token must only be used in dev (`import.meta.env.DEV`); production builds must not embed it. Flag to Security for review (a browser-held token is not secret).
- Follow API_CONTRACT.md exactly; if mismatched, stop and notify the Team Leader.
- Vitest tests with mocked axios: success, wrong password, network error.

## Acceptance Criteria
- [x] With the backend running, Home displays Healthy; with it stopped, a friendly error state shows
- [x] Base URL comes only from env; no URL hardcoded in components
- [x] Tests written and passing; lint clean

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — frontend: Added axios instance (src/api/http.js, env baseURL, ApiError normalisation, JWT interceptor placeholder), api/health.js (token header only when import.meta.env.DEV), stores/health.js, components/HealthStatus.vue on Home (loading/healthy/error+retry). 17 frontend tests passing, lint clean, build OK. Verified against the running backend with curl: 200 envelope, CORS allows origin and x-health-check-token. Not verified in a real browser. Flag for Security: VITE_HEALTH_CHECK_TOKEN is browser-visible in dev. Status IN_REVIEW.
- 2026-10-10 — qa: TASK-022 frontend QA PASS (QA_REPORT.md; 30/30 real-browser cases, 47 unit tests); status DONE.
- 2026-10-10 — frontend: PO decision: production health is checked server-side (curl, tests, Sentry). HomeView now renders HealthStatus only when import.meta.env.DEV; no health call or header in production bundles. 49 tests passing.
