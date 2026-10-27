# TASK-007: Idempotent demo data command (seed_demo)

- **Backlog item:** BL-007
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-006
- **Estimate:** M

## Description
Add an optional documented `seed_demo` command loading demo data, safe to run repeatedly.

## Technical Notes
- Only models that exist in Sprint 01 can be seeded now: demo Admin, Manager and sample Driver/Trader/Client users (shops, items, locations, orders do not exist yet). Build the command as a registry of per-app seeders (`apps/<app>/seeders.py`) so later sprints add shops, items, clients' locations and orders in various statuses without changing the command. Record this limitation in the README and Activity Log.
- Use `update_or_create` on natural keys (username) so a second run creates no duplicates and does not break data; run inside one transaction.
- Refuse to run when `DEBUG=False` unless `--force`. Demo passwords come from env `DEMO_PASSWORD`, no hardcoded real-looking secrets. Add `make seed-demo`; document in README.

## Acceptance Criteria
- [x] Running `seed_demo` twice yields identical row counts
- [x] Refuses in production-like settings without `--force`
- [x] Demo users have correct roles (Admin, Manager, Driver, Trader, Client)
- [x] Tests written and passing

## Activity Log
- 2026-10-08 — team_leader: Task created for sprint-01.
- 2026-10-10 — backend: Implemented apps/core seed_demo command + apps/users/seeders.py registry, make seed-demo, README, DEMO_PASSWORD in .env.example, tests (5). Full suite 74+ passing, ruff clean. Limitation: only users seeded in Sprint 01; shops/items/locations/orders to be added by later seeders. Status IN_REVIEW.
- 2026-10-10 — qa: TASK-021 backend QA PASS (see QA_REPORT.md); status DONE.
