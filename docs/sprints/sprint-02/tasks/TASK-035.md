# TASK-035: Router: role areas, guards and redirects

- **Backlog item:** BL-008, BL-012, BL-013
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-034
- **Estimate:** M

## Description
Turn the Sprint 01 placeholder areas into guarded areas.

## Technical Notes
- Routes meta: `public`, `roles`. Guard: unauthenticated -> `/login`; wrong role -> redirected to own home (or a friendly 'not allowed' view); logged-in users visiting login/register -> own home.
- Role to home: driver `/driver` (My Assigned Orders), trader `/trader` (Dashboard), client `/client` (Home), admin and manager `/admin` (Dashboard).
- Guards use the store, not the token text; a 401/403 from the API also leads to the right redirect. Keep the 404 route and the bottom navigation consistent with the user's role (show only own area plus logout).

## Acceptance Criteria
- [x] Direct URL to another role's area is refused
- [x] After logout protected URLs redirect to login
- [x] Unit tests for the guard matrix (4 roles x public/protected x logged in/out)
- [x] Lint clean; tests passing
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-15 — frontend: Implemented route meta (public/roles/guestOnly), auth guard (awaits session restore), login/register placeholder routes, role-aware bottom nav + logout, 403 handler. Added guards.spec.js (54 tests); suite 131/131 passing, eslint clean. Status IN_REVIEW.
- 2026-10-16 — frontend: BUG-009 fix: added `scroll-padding-bottom` (nav height + safe-area + 1rem) on `html` in src/assets/main.css so focused fields are not hidden under the fixed bottom nav; test in register.spec.js. Suite 178/178, eslint clean. Status IN_REVIEW; ready for QA retest.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results (frontend)" (TASK-040 APPROVED, retest 120/120 on 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
