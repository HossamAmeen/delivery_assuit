# Sprint 01

- **Goal:** Project init: runnable Django + DRF backend, Vue 3 frontend, Docker environment, CI, bilingual (AR/EN, RTL/LTR) shell and PWA, with the frontend calling the backend health check end to end.
- **Status:** DONE (2026-10-11). QA and Security passed; E2 real-device PWA install check left as the last item in docs/TODO.md (PO: ignore for now). CI deferred to the end.
- **Approval to start:** APPROVED by PO on 2026-10-08

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-001 | Backend project skeleton | SEC-01 | Must | backend |
| BL-002 | Frontend project skeleton | SEC-01 | Must | frontend |
| BL-003 | Containerized development environment | SEC-01 | Must | both |
| BL-004 | Continuous integration pipeline | SEC-01 | Should | both |
| BL-005 | Installable PWA shell | SEC-01 | Should | frontend |
| BL-006 | Bilingual support (Arabic + English, RTL/LTR) | SEC-01 | Must | frontend |
| BL-007 | Seed/demo data and initial admin account | SEC-01 | Must | backend |

## Carry-over from previous sprint
- None (first sprint).

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] Backend + QA signed APPROVAL.md

## Risks
- BL-006 (bilingual) is Must and is built here so every later screen is bilingual from the start.
- Scope of the PWA shell is limited to installability; no feature screens yet.
