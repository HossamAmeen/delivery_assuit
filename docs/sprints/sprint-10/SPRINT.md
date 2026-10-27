# Sprint 10

- **Goal:** Polish: in-app notifications, auto-refresh, UX improvements, and an audit trail.
- **Status:** BUILT, awaiting QA (started 2026-10-27). Backend TASK-132..134 and frontend TASK-135..138 are IN_REVIEW. QA TASK-139 paused by PO until staging upload. Nothing run in a browser or against a live server.
- **Approval to start:** GRANTED by the PO on 2026-10-27

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-066 | In-app notifications | SEC-10 | Should | both |
| BL-067 | Auto-refresh of order data | SEC-10 | Could | both |
| BL-068 | Basic UX improvements | SEC-10 | Should | frontend |
| BL-069 | Account and action audit trail | SEC-10 | Could | backend |

## Carry-over from previous sprint
- None at planning time. Unfinished or rejected items from sprint-09 move here.

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] Backend + QA signed APPROVAL.md

## Risks
- All items are Could/Should; scope may be trimmed to protect the schedule.
- Notifications are in-app only (no push/SMS).

## Tasks (TASK-132..139)
| Task | Assignee | Title |
|------|----------|-------|
| TASK-132 | backend | API contract for Sprint 10 |
| TASK-133 | backend | In-app notifications |
| TASK-134 | backend | Audit trail |
| TASK-135 | frontend | Notifications bell and list |
| TASK-136 | frontend | Auto-refresh of order screens |
| TASK-137 | frontend | UX consistency and confirmations |
| TASK-138 | frontend | Audit log screen |
| TASK-139 | qa | QA for Sprint 10 |

QA TASK-139 paused by the PO until the staging upload.
