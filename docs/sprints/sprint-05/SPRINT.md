# Sprint 05

- **Goal:** Order creation and review: a client browses shops and orders from a shop or requests a direct place-to-place delivery; Admin/Manager reviews and approves it so it becomes AVAILABLE with a valid lifecycle and strict visibility rules.
- **Status:** BUILT, awaiting QA (started 2026-10-27). Backend TASK-076..081 and frontend TASK-082..085 are IN_REVIEW. QA TASK-086/087 paused by PO until staging upload. Nothing run in a browser or against a live server.
- **Approval to start:** GRANTED by the PO on 2026-10-27

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-021 | Order data and unique reference | SEC-04 | Must | backend |
| BL-022 | Order status lifecycle and allowed transitions | SEC-04 | Must | backend |
| BL-024 | Order visibility and permissions | SEC-04 | Must | backend |
| BL-023 | Admin/Manager reviews orders before they become available | SEC-04 | Must | both |
| BL-045 | Browse available shops | SEC-07 | Must | both |
| BL-046 | Shop details | SEC-07 | Must | both |
| BL-047 | Order from a shop (Scenario C) | SEC-07 | Must | both |
| BL-048 | Direct place-to-place delivery (Scenario D) | SEC-07 | Must | both |

## Carry-over from previous sprint
- None at planning time. Unfinished or rejected items from sprint-04 move here.

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] Backend + QA signed APPROVAL.md

## Risks
- Orders are created by clients only (BR-18); trader-created orders (BL-037) are Later Phase.
- Eight items; BL-048 can slip to Sprint 06 if the schedule is tight, as the shop flow is the core cycle.
- Orders have no fee until BL-077 (Sprint 07); the fee is shown as not set.

## Tasks (TASK-076..087)
| Task | Assignee | Title |
|------|----------|-------|
| TASK-076 | backend | API contract for Sprint 05 |
| TASK-077 | backend | Order models, reference, and lifecycle service |
| TASK-078 | backend | Order visibility and read endpoints |
| TASK-079 | backend | Browse shops and shop details for clients |
| TASK-080 | backend | Create order: shop order and direct delivery |
| TASK-081 | backend | Order review: approve and reject |
| TASK-082 | frontend | Client shops list and shop details screens |
| TASK-083 | frontend | Order from a shop screen |
| TASK-084 | frontend | Direct delivery screen |
| TASK-085 | frontend | Admin review screen |
| TASK-086 | qa | Backend QA for Sprint 05 |
| TASK-087 | qa | Frontend QA for Sprint 05 |

Order: backend 076 to 081, then frontend 082 to 085. QA 086/087 paused by the PO until the staging upload.
