# TASK-038: Role home screens, user menu and logout

- **Backlog item:** BL-012, BL-013
- **Assignee:** frontend
- **Status:** DONE
- **Depends on:** TASK-035, TASK-036
- **Estimate:** M

## Description
Replace the empty placeholders with role-specific home screens and add logout.

## Technical Notes
- Four home screens with the agreed titles and an empty-state body (real content comes in later sprints): Driver 'My Assigned Orders', Trader 'Dashboard', Client 'Home', Admin/Manager 'Dashboard'. Show the user's name and role.
- Header user menu with Logout (clears store and storage, calls `/auth/logout/`, goes to login). Logout works even if the API call fails.
- Session-expired handling: refresh failure shows a short notice on the login screen.

## Acceptance Criteria
- [x] After logout protected screens redirect to login and old refresh token is blacklisted
- [x] Each role lands on its own home after login
- [x] Component tests; lint clean; tests passing
- [x] Tests written and passing

## Activity Log
- 2026-10-11 — team_leader: Task created for sprint-02.
- 2026-10-16 — frontend: Implemented role home screens (AreaHomeView), header user menu with logout (AppHeader; bottom-nav Sign out removed), 175 Vitest tests passing, eslint clean. Status IN_REVIEW.
- 2026-10-24 — team_leader: Status set to DONE. QA passed this task: QA_REPORT.md "Task results (frontend)" (TASK-040 APPROVED, retest 120/120 on 2026-10-16); included in the Sprint 02 APPROVAL.md sign-offs (2026-10-17).
