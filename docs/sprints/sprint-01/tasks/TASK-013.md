# TASK-013: Frontend sends language header and shows localized server errors

- **Backlog item:** BL-006
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-011, TASK-012, TASK-009
- **Estimate:** S

## Description
Connect the frontend language to the backend so server error messages appear in the user's language (BL-006 AC4).

## Technical Notes
- Axios request interceptor adds `Accept-Language` from the language store.
- Error handling shows `message` from the envelope as returned (already localized by the server); fall back to a locale-file generic message on network failure.
- Re-fetch/refresh visible health status text on language change.

## Acceptance Criteria
- [x] Health failure message appears in Arabic when UI is Arabic and English when English (verified against the real backend)
- [x] Network failure shows a localized fallback
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — frontend: Axios request interceptor sends Accept-Language from the active i18n locale; ApiError.message is the server text as returned (empty when none) and the UI shows it, falling back to localized locale-file text on network failure; HealthStatus re-fetches on language change. 31 tests passing, lint clean, build OK. Verified against the real backend with curl (wrong token: Arabic message for ar, English for en; CORS preflight OK, Accept-Language is a CORS-safelisted header). The full browser round trip was not exercised. Status IN_REVIEW.
- 2026-10-10 — qa: TASK-022 frontend QA PASS (QA_REPORT.md; 30/30 real-browser cases, 47 unit tests); status DONE.
