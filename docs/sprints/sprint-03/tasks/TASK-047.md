# TASK-047: Profile edit and unique email

- **Backlog item:** BL-015; VULN-018 (email half only)
- **Assignee:** backend
- **Status:** IN_REVIEW
- **Depends on:** TASK-044
- **Estimate:** M

## Description
The caller can read their profile (already `GET /auth/me/`) and update their own name, phone, and email. They cannot change role, status, or username here.

## Technical Notes
- `PATCH /api/v1/auth/me/` as in the contract. Permission `IsOperational`.
- `full_name` 2–255, trimmed. `phone` uses the existing normaliser and stays unique. `email` may be cleared back to empty. A non-empty email is stripped, lower-cased, and unique.
- Migration: a unique constraint on `Lower(email)` for rows where `email` is not `''`. Many empty emails stay allowed. Map an integrity error to 400 `errors.email` ("A user with this email already exists."), same as the registration message.
- If the body contains `role`, `status`, or `username`, return 400 and change nothing.
- A user can only touch their own row. No id in the URL.
- Phone OTP is out of scope. Do not add a verification flag.
- Keep `GET /auth/me/` as it is, including the new fields once they exist (`rejection_reason` may be added by TASK-049; do not block this task on it).

## Acceptance Criteria
- [x] A user sees name, phone, username, email, role, and status
- [x] Name, phone, and email can be updated; phone and email stay unique
- [x] Role, status, and username cannot be changed through this endpoint
- [~] Two concurrent non-empty emails that differ only by case cannot both commit
- [x] Tests written and passing; `makemigrations --check` clean

## Activity Log
- 2026-10-26 — team_leader: Task created for BL-015. Phone OTP deliberately excluded.
- 2026-10-27 — backend: `PATCH /auth/me/` added (own row only, `IsOperational`; `GET /auth/me/` now uses the same permission). Migration `0003_user_email_unique`: unique on `Lower(email)` for non-empty emails of non-deleted users. Role, status, and username are refused with 400 and nothing is saved. Phone and email duplicates exclude the caller's own row. A lost race maps to 400 on the right field (registration too: it used to report a phone error for an email race). 23 new tests; full suite 339 passed, 1 skipped; ruff clean; `makemigrations --check` clean. The skipped test is the real two-thread email race: it needs PostgreSQL, so it was not run (the DB constraint itself is tested on SQLite). Arabic strings added. Status IN_REVIEW. QA has not tested it yet.
