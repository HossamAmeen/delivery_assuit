# Sprint 09

- **Goal:** Performance and ratings: clients rate drivers after delivery, drivers see monthly performance, Admin/Manager sees the dashboard with a time filter and a driver performance overview, and order lists can be filtered and searched.
- **Status:** BUILT, awaiting QA (started 2026-10-27). Backend TASK-122..125 and frontend TASK-126..130 are IN_REVIEW. QA TASK-131 paused by PO until staging upload. Nothing run in a browser or against a live server.
- **Approval to start:** GRANTED by the PO on 2026-10-27

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-061 | Rating data model and rules | SEC-09 | Should | backend |
| BL-062 | Driver performance calculation | SEC-09 | Must | backend |
| BL-051 | Rate driver after delivery | SEC-07 | Should | both |
| BL-063 | Driver performance screen | SEC-09 | Must | both |
| BL-060 | Overview of driver performance | SEC-08 | Must | both |
| BL-053 | Dashboard cards with time filter | SEC-08 | Must | both |
| BL-028 | Order list filtering and search | SEC-04 | Should | both |

## Carry-over from previous sprint
- None at planning time. Unfinished or rejected items from sprint-08 move here.

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] Backend + QA signed APPROVAL.md

## Risks
- Rating is optional for the client; BR-10 defines performance from executed orders and ratings.

## Tasks (TASK-122..131)
| Task | Assignee | Title |
|------|----------|-------|
| TASK-122 | backend | API contract for Sprint 09 |
| TASK-123 | backend | Ratings: model, rules and endpoint |
| TASK-124 | backend | Driver performance calculation, driver endpoint and staff overview |
| TASK-125 | backend | Staff dashboard counts with a period filter |
| TASK-126 | frontend | Client rates the driver |
| TASK-127 | frontend | Driver performance screen |
| TASK-128 | frontend | Staff driver performance overview |
| TASK-129 | frontend | Admin dashboard cards with a time filter |
| TASK-130 | frontend | Order list search by reference |
| TASK-131 | qa | QA for Sprint 09 |

QA TASK-131 paused by the PO until the staging upload.
