# Sprint 07

- **Goal:** Admin/Manager operations and pricing: Admin/Manager sets delivery fee and item prices, sees all orders, cancels orders, and manages drivers, traders, and clients including trader approval effects.
- **Status:** BUILT, awaiting QA (started 2026-10-27). Backend TASK-098..106 and frontend TASK-107..111 are IN_REVIEW. QA TASK-112 paused by PO until staging upload. Nothing run in a browser or against a live server.
- **Approval to start:** GRANTED by the PO on 2026-10-27

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-077 | Admin/Manager sets delivery fee and item prices | SEC-08 | Must | both |
| BL-054 | Admin/Manager orders table | SEC-08 | Must | both |
| BL-025 | Cancel order | SEC-04 | Must | both |
| BL-055 | Admin/Manager cancels orders | SEC-08 | Should | both |
| BL-043 | Trader approval and status effects | SEC-06 | Must | both |
| BL-056 | Admin drivers management | SEC-08 | Must | both |
| BL-057 | Admin traders/shops management | SEC-08 | Must | both |
| BL-058 | Admin clients management | SEC-08 | Should | both |

## Carry-over from previous sprint
- None at planning time. Unfinished or rejected items from sprint-06 move here.

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] Backend + QA signed APPROVAL.md

## Risks
- BR-12: the client may cancel only before assignment; after assignment only Admin/Manager can cancel; a DELIVERED order cannot be cancelled.
- Eight items; BL-058 (Should) can be trimmed first.

## Tasks (TASK-098..112)
| Task | Assignee | Title |
|------|----------|-------|
| TASK-098 | backend | API contract for Sprint 07 |
| TASK-099 | backend | Item prices by staff and price snapshot on order lines |
| TASK-100 | backend | Delivery fee changes with history |
| TASK-101 | backend | Orders table filters and status timeline |
| TASK-102 | backend | Cancel order |
| TASK-103 | backend | Trader approval and status effects |
| TASK-104 | backend | Staff drivers list and detail |
| TASK-105 | backend | Staff traders list and detail |
| TASK-106 | backend | Staff clients list and detail |
| TASK-107 | frontend | Admin orders table |
| TASK-108 | frontend | Staff order details: timeline, fee, cancel, actions |
| TASK-109 | frontend | Staff management lists |
| TASK-110 | frontend | Staff management details |
| TASK-111 | frontend | Trader pending and inactive message |
| TASK-112 | qa | QA for Sprint 07 |

QA TASK-112 paused by the PO until the staging upload.
