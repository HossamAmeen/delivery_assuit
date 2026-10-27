# Sprint 04

- **Goal:** Locations, shop setup, and client home: traders manage locations and shop profile and items; clients manage delivery locations and saved addresses and see their home screen.
- **Status:** BUILT, awaiting QA (started 2026-10-27). Backend TASK-065..069 and frontend TASK-070..073 are IN_REVIEW. QA TASK-074/075 paused by PO until staging upload. Nothing run in a browser or against a live server.
- **Approval to start:** GRANTED by the PO on 2026-10-27 ("do up to 8 tasks")

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-017 | Trader manages locations/branches | SEC-03 | Must | both |
| BL-018 | Mark a location as usable for pickup and/or delivery | SEC-03 | Should | both |
| BL-019 | Location input for client orders | SEC-03 | Must | both |
| BL-020 | Shop's default pickup location | SEC-03 | Must | both |
| BL-041 | Trader shop profile and availability | SEC-06 | Must | both |
| BL-042 | Shop items list (simple) | SEC-06 | Must | both |
| BL-044 | Client home | SEC-07 | Must | frontend |
| BL-076 | Client saved addresses | SEC-07 | Should | both |

## Carry-over from previous sprint
- None at planning time. Unfinished or rejected items from sprint-03 move here.

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] Backend + QA signed APPROVAL.md

## Risks
- Only simple shop items are in scope; the full catalog (BL-074) is Later Phase.
- Item prices are set by Admin/Manager (BR-17), delivered in Sprint 07 (BL-077); items have no price until then.

## Tasks (TASK-065..075)
| Task | Assignee | Title |
|------|----------|-------|
| TASK-065 | backend | API contract for Sprint 04 |
| TASK-066 | backend | Trader locations (CRUD, pickup/delivery flags, default pickup) |
| TASK-067 | backend | Shop profile and availability |
| TASK-068 | backend | Shop items (flat list, hide, no price) |
| TASK-069 | backend | Client saved addresses |
| TASK-070 | frontend | Trader locations screens |
| TASK-071 | frontend | Trader shop profile and items screens |
| TASK-072 | frontend | Client home |
| TASK-073 | frontend | Client saved addresses screens |
| TASK-074 | qa | Backend QA for Sprint 04 |
| TASK-075 | qa | Frontend QA for Sprint 04 |

Order: 065 first, then 066, 067, 068, 069 (backend), then 070, 071, 072, 073 (frontend). QA 074/075 stays paused by the PO until the staging upload.
