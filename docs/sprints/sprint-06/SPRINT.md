# Sprint 06

- **Goal:** Assignment and driver execution: Admin/Manager assigns an AVAILABLE order to an approved driver; the driver sees assigned orders and moves them to DELIVERED, completing the core MVP cycle.
- **Status:** BUILT, awaiting QA (started 2026-10-27). Backend TASK-088..091 and frontend TASK-092..096 are IN_REVIEW. QA TASK-097 paused by PO until staging upload. Nothing run in a browser or against a live server.
- **Approval to start:** GRANTED by the PO on 2026-10-27

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-031 | Admin/Manager assigns an order to a driver | SEC-05 | Must | both |
| BL-029 | View my assigned orders | SEC-05 | Must | both |
| BL-030 | Order details for driver | SEC-05 | Must | both |
| BL-032 | Execute order - pickup, in delivery, delivered | SEC-05 | Must | both |
| BL-033 | Driver's active order view | SEC-05 | Must | frontend |
| BL-034 | My Orders (previous orders) | SEC-05 | Must | both |
| BL-036 | Driver profile | SEC-05 | Must | both |

## Carry-over from previous sprint
- None at planning time. Unfinished or rejected items from sprint-05 move here.

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] Backend + QA signed APPROVAL.md

## Risks
- Assumption (BR-1, unconfirmed by the PO): a driver holds one active order at a time; assignment must be blocked for a driver with an active order.
- Drivers never self-accept; there is no accept, un-accept, or release (BR-4); BL-035 is retired.
- Contact phones become visible to the driver only after assignment (BR-16); needs a dedicated permission test.
- Assumption: traders and clients see the assigned driver's name only; the driver's phone is not exposed to them.

## Tasks (TASK-088..097)
| Task | Assignee | Title |
|------|----------|-------|
| TASK-088 | backend | API contract for Sprint 06 |
| TASK-089 | backend | Assign an order to a driver, and the drivers list |
| TASK-090 | backend | Driver execution: advance an order |
| TASK-091 | backend | Driver lists, details, and contact numbers |
| TASK-092 | frontend | Admin assign screen |
| TASK-093 | frontend | Driver home: active order |
| TASK-094 | frontend | Driver order details and next-step button |
| TASK-095 | frontend | Driver My Orders (history) |
| TASK-096 | frontend | Driver profile and navigation |
| TASK-097 | qa | Backend and frontend QA for Sprint 06 |

Order: backend 088 to 091, then frontend 092 to 096. QA 097 paused by the PO until the staging upload. BL-035 is retired.
