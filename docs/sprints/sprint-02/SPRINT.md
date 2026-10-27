# Sprint 02

- **Goal:** Accounts: users register as Driver, Trader, or Client, log in by phone or username, and log out, landing on a role-specific home screen.
- **Status:** APPROVED WITH EXCEPTIONS (PO accepted E1–E4 on 2026-10-26; see `APPROVAL.md`). Not deployed. E2 remains a hard gate before any staging or production deploy. TASK-042 stays open and moves to Sprint 03.
- **Approval to start:** APPROVED by the PO on 2026-10-11
- **Scope note (2026-10-17):** PO decision (2026-10-17): Sprint 02 scope for the security fixes = TASK-041 and TASK-043 only; TASK-042 (VULN-012) is deferred to Sprint 03. TASK-041 and TASK-043 are DONE (QA and Security retest passed 2026-10-17).

## Scope
| ID | Title | Section | Priority | Scope |
|----|-------|---------|----------|-------|
| BL-008 | User roles and role-based access | SEC-02 | Must | backend |
| BL-009 | Driver registration | SEC-02 | Must | both |
| BL-010 | Trader/Shop registration | SEC-02 | Must | both |
| BL-011 | Client registration | SEC-02 | Must | both |
| BL-012 | Login (phone or username) | SEC-02 | Must | both |
| BL-013 | Logout | SEC-02 | Must | both |

## Carry-over from previous sprint
- Sprint 01 E2: real-device PWA install check (LAST item in `docs/TODO.md`; PO said to ignore it for now).
- CI (TASK-019/020) and DevOps deploy files are deferred to the end (PO).
- No local Docker (PO). Tests run with the venv and npm; QA uses live servers without Docker.

## Definition of Done
- [ ] All tasks DONE and passed QA
- [ ] Backend tests pass, coverage >= 80% on new code
- [ ] No Critical/High security findings open
- [ ] Backend + QA signed APPROVAL.md

## Risks
- Drivers and traders cannot operate until approved (BR-15); the approval screen arrives in Sprint 03, so until then use seeded accounts for demo.
- Assumption: username is an optional unique profile field for all roles (always set for Admin/Manager); drivers still register with name, phone, password only.

## Tasks (TASK-027..043; TASK-042 deferred to Sprint 03)
| Task | Assignee | Title |
|------|----------|-------|
| TASK-027 | backend | API contract (contract first) |
| TASK-028 | backend | User status field and registration rules |
| TASK-029 | backend | Role permission classes and `/auth/me/` |
| TASK-030 | backend | Registration endpoints (Driver, Trader, Client) |
| TASK-031 | backend | Login update: status checks, user summary |
| TASK-032 | backend | Logout, refresh rotation and blacklist |
| TASK-033 | backend | seed_demo per role and status |
| TASK-034 | frontend | Auth API service, tokens, Pinia store |
| TASK-035 | frontend | Router guards and role areas |
| TASK-036 | frontend | Login screen |
| TASK-037 | frontend | Registration screens |
| TASK-038 | frontend | Role home screens, user menu, logout |
| TASK-039 | qa | Backend QA |
| TASK-040 | qa | Frontend QA |

Order: 027 first; backend 028 to 033; frontend 034 can start after 027; 035 to 038 follow; QA last. Then Security review of the sprint.

## Security fix tasks (from SECURITY_REPORT.md, Team Leader triage 2026-10-17)
Release decision was PASS (0 Critical/High). The three Medium findings became fix tasks. Scope is a PO decision; recommendation:

| Task | Finding | Assignee | Recommendation |
|------|---------|----------|----------------|
| TASK-041 | VULN-011 atomic refresh rotation | backend | Sprint 02 (small; completes the VULN-009 fix) |
| TASK-042 | VULN-012 refresh token in localStorage, no CSP | frontend (+devops) | Interim hardening may join Sprint 02; cookie redesign deferred to Sprint 03 (PO decision) |
| TASK-043 | VULN-013 staging port 8000 exposed with NUM_PROXIES=1 | devops | Sprint 02 (config edit); hard gate before any staging/production deploy |

### Deferred / triage candidates (no tasks created)
| Finding | Sev | Suggested home |
|---------|-----|----------------|
| VULN-014 500 on deep JSON / oversized body / odd claim | Low | Backend hardening batch (Sprint 03) + Nginx `client_max_body_size` (DevOps) |
| VULN-015 login identifier/password unbounded length | Low | Backend hardening batch; trivial `max_length` |
| VULN-016 lenient identifier normalisation | Low | Backend hardening batch |
| VULN-017 no reuse detection; sessions survive password change | Low | Sprint 03 with password recovery (must be done there at the latest); can pair with TASK-041 |
| VULN-018 unverified phone/email, no DB unique email | Low | Sprint 03 (OTP/recovery) |
| VULN-019 token responses not `Cache-Control: no-store` | Low | Backend hardening batch (small middleware) |
| VULN-020 dev SECRET_KEY fallback (Info) | Info | Accept; keep dev servers off public networks |
| VULN-021 seed_demo superuser (Info) | Info | Optional: refuse when settings module is staging/production |
| VULN-022 per-IP only shared auth throttle (Info) | Info | Revisit with per-identifier limits in Sprint 03 |

## Decisions to flag for Security (Team Leader)
- Access token in memory, refresh token in `localStorage` (needed to stay signed in after a refresh). Risk: an XSS bug could read it. Mitigations: no `v-html`, rotation + blacklist, short access lifetime. An httpOnly-cookie design is the alternative (more setup with CORS/CSRF); Security to review.
- Registration shows that a phone number is already used (required by the acceptance criteria); it is rate-limited.
