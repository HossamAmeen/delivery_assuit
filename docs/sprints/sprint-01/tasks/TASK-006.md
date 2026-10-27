# TASK-006: Management command to create the first Admin account

- **Backlog item:** BL-007
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-005
- **Estimate:** S

## Description
Add a documented command that creates the first Admin without using public registration.

## Technical Notes
- Command: `python manage.py create_admin --username X [--phone P] [--email E]`; password from prompt, or from env `ADMIN_PASSWORD` for non-interactive Docker use. Never accept the password as a plain CLI argument.
- Idempotent: if the username exists, exit with a clear message and no change (or `--update-password`).
- Add `make create-admin`. No credentials committed; `.env.example` documents `ADMIN_USERNAME`/`ADMIN_PASSWORD` placeholders.
- Document in the backend README.

## Acceptance Criteria
- [ ] Command creates a user with role Admin, is_staff and is_superuser true, usable to log into /admin and get a JWT
- [ ] Running twice does not duplicate or error destructively
- [ ] No password printed or logged
- [ ] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-09 — backend: Implemented apps/users create_admin command (password from ADMIN_PASSWORD or prompt, idempotent, --update-password), make create-admin, .env.example placeholders, README section, 10 tests. check/makemigrations/ruff/make test pass. Status IN_REVIEW.
- 2026-10-10 — qa: TASK-021 backend QA PASS (see QA_REPORT.md); status DONE.
