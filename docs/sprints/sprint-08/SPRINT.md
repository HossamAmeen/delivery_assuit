# Sprint 08

- **Goal:** Trader and client tracking: traders follow orders placed to their shop and see the assigned driver and a dashboard; clients list and track own orders with a status timeline and edit before assignment.
- **Status:** BUILT, awaiting QA (started 2026-10-27). Backend TASK-113..115 and frontend TASK-116..120 are IN_REVIEW. QA TASK-121 paused by PO until staging upload. Nothing run in a browser or against a live server.
- **Approval to start:** GRANTED by the PO on 2026-10-27

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-038 | Trader's orders list and tracking | SEC-06 | Must | both |
| BL-039 | See the assigned driver | SEC-06 | Must | both |
| BL-040 | Trader dashboard | SEC-06 | Should | both |
| BL-049 | Client's orders list | SEC-07 | Must | both |
| BL-050 | Client order details and tracking | SEC-07 | Must | both |
| BL-027 | Order status history | SEC-04 | Should | both |
| BL-026 | Edit order before driver assignment | SEC-04 | Should | both |

## Carry-over from previous sprint
- None at planning time. Unfinished or rejected items from sprint-07 move here.

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] Backend + QA signed APPROVAL.md

## Risks
- Assumption: traders and clients see the assigned driver's name only; the driver's phone is not exposed to them.
- BR-13: edits are allowed only before a driver is assigned; needs a test for the boundary.
- BL-040 (Should) can be trimmed to protect the schedule.

## Tasks (TASK-113..121)
| Task | Assignee | Title |
|------|----------|-------|
| TASK-113 | backend | API contract for Sprint 08 |
| TASK-114 | backend | Orders summary counts |
| TASK-115 | backend | Edit an order before assignment |
| TASK-116 | frontend | Trader orders list and details |
| TASK-117 | frontend | Trader dashboard counts |
| TASK-118 | frontend | Client orders list |
| TASK-119 | frontend | Client order details, tracking and cancel |
| TASK-120 | frontend | Client edit order |
| TASK-121 | qa | QA for Sprint 08 |

BL-027 backend (timeline) and BL-025 cancel were built in Sprint 07. QA TASK-121 paused by the PO until the staging upload.
