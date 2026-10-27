# Roadmap

Excluded (Later Phase, SEC-11): BL-037, BL-074, BL-070 to BL-073, BL-075. BL-035 is retired. 70 items across 10 sprints. Flow: client creates, Admin/Manager reviews, Admin/Manager assigns a driver, driver executes.

| Sprint | Goal | Items | Depends on | Status |
|--------|------|-------|-----------|--------|
| [Sprint 01](sprint-01/SPRINT.md) | Project init: runnable Django + DRF backend, Vue 3 frontend, Docker environment, CI, bilingual (AR/EN, RTL/LTR) shell and PWA, with the frontend calling the backend health check end to end. | BL-001, BL-002, BL-003, BL-004, BL-005, BL-006, BL-007 | - | DONE (QA + Security passed; PWA real-device check left on TODO) |
| [Sprint 02](sprint-02/SPRINT.md) | Accounts: users register as Driver, Trader, or Client, log in by phone or username, and log out, landing on a role-specific home screen. | BL-008, BL-009, BL-010, BL-011, BL-012, BL-013 | Sprint 01 | APPROVED WITH EXCEPTIONS (PO accepted E1–E4 on 2026-10-26; not deployed; TASK-042 carried to Sprint 03) |
| [Sprint 03](sprint-03/SPRINT.md) | Account management: users manage profile, password, and email recovery; Admin/Manager manage users and Manager accounts, activate/deactivate accounts, and approve driver and trader registrations; consistent validation and UI states. | BL-014, BL-015, BL-016, BL-052, BL-059, BL-064, BL-065, BL-078 | Sprint 01, Sprint 02 | IN_PROGRESS (TASK-044 DONE; TASK-045 and TASK-054 IN_REVIEW; VULN-012 = cookie) |
| [Sprint 04](sprint-04/SPRINT.md) | Locations, shop setup, and client home: traders manage locations and shop profile and items; clients manage delivery locations and saved addresses and see their home screen. | BL-017, BL-018, BL-019, BL-020, BL-041, BL-042, BL-044, BL-076 | Sprint 02, Sprint 03 | PLANNED |
| [Sprint 05](sprint-05/SPRINT.md) | Order creation and review: a client browses shops and orders from a shop or requests a direct place-to-place delivery; Admin/Manager reviews and approves it so it becomes AVAILABLE with a valid lifecycle and strict visibility rules. | BL-021, BL-022, BL-024, BL-023, BL-045, BL-046, BL-047, BL-048 | Sprint 02, Sprint 04 | PLANNED |
| [Sprint 06](sprint-06/SPRINT.md) | Assignment and driver execution: Admin/Manager assigns an AVAILABLE order to an approved driver; the driver sees assigned orders and moves them to DELIVERED, completing the core MVP cycle. | BL-031, BL-029, BL-030, BL-032, BL-033, BL-034, BL-036 | Sprint 03, Sprint 05 | PLANNED |
| [Sprint 07](sprint-07/SPRINT.md) | Admin/Manager operations and pricing: Admin/Manager sets delivery fee and item prices, sees all orders, cancels orders, and manages drivers, traders, and clients including trader approval effects. | BL-077, BL-054, BL-025, BL-055, BL-043, BL-056, BL-057, BL-058 | Sprint 02, Sprint 03, Sprint 04, Sprint 05 | PLANNED |
| [Sprint 08](sprint-08/SPRINT.md) | Trader and client tracking: traders follow orders placed to their shop and see the assigned driver and a dashboard; clients list and track own orders with a status timeline and edit before assignment. | BL-038, BL-039, BL-040, BL-049, BL-050, BL-027, BL-026 | Sprint 05, Sprint 06 | PLANNED |
| [Sprint 09](sprint-09/SPRINT.md) | Performance and ratings: clients rate drivers after delivery, drivers see monthly performance, Admin/Manager sees the dashboard with a time filter and a driver performance overview, and order lists can be filtered and searched. | BL-061, BL-062, BL-051, BL-063, BL-060, BL-053, BL-028 | Sprint 02, Sprint 05, Sprint 06, Sprint 08 | PLANNED |
| [Sprint 10](sprint-10/SPRINT.md) | Polish: in-app notifications, auto-refresh, UX improvements, and an audit trail. | BL-066, BL-067, BL-068, BL-069 | Sprint 01, Sprint 03, Sprint 05, Sprint 06, Sprint 08 | PLANNED |

## Rules

- Before starting each new sprint, the user must be asked and must approve; do not begin the next sprint (task breakdown or implementation) without explicit approval.
- Every sprint stays PLANNED until approval is given. Each SPRINT.md records this under Status as "Approval to start".
- Unfinished or rejected items carry over to the next sprint; scope changes go back to the Business Manager.
- Assumptions listed in a sprint's Risks should be confirmed with the Product Owner before that sprint starts.
