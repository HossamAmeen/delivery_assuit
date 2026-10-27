# TASK-042: Reduce refresh-token exposure in the browser: CSP and lint guard now, cookie design decided later (VULN-012)

- **Backlog item:** BL-009..BL-013 (auth session); security fix for VULN-012 (Medium)
- **Assignee:** frontend (interim part); backend + frontend + devops for the cookie design (new tasks in Sprint 03 if the PO chooses it)
- **Status:** TODO
- **Depends on:** TASK-034 (DONE); the cookie option also needs backend changes (new task, not created yet)
- **Estimate:** S (interim part) / L (cookie design)
- **Scope recommendation:** **Split.** (a) Interim hardening (ESLint `vue/no-v-html` as error, strict CSP as a documented Nginx header plus a CSP meta/dev-compatible check, shorter refresh lifetime for admin/manager decision) can go in **Sprint 02** if the PO wants it; it is low risk and needs no API change. (b) Moving the refresh token to an `HttpOnly; Secure; SameSite=Strict` cookie scoped to `/api/v1/auth/` (needs CSRF/origin check, CORS credentials, contract change, store rewrite, retest of all auth QA) is **deferred to Sprint 03**, designed together with password recovery and VULN-017. Reason: it changes the API contract and the whole Sprint 02 QA surface; doing it now would reopen QA and Security. No XSS sink exists today (Security checked), so the risk is a hardening gap, not an exploitable bug. PO decision needed on (b).

## Description
The 7-day refresh token is stored in `localStorage` (`delivery.refresh_token`) and the app has no CSP. A future XSS or malicious dependency would give persistent account takeover.

## Technical Notes
- Interim (a): enable ESLint `vue/no-v-html: error` in `frontend/`; add a CSP (`default-src 'self'`; no inline scripts; `frame-ancestors 'none'`; `connect-src` for the API origin) as a header snippet for the Nginx template (DevOps file, handed to TASK-043 area) and verify the production build runs under it; keep dev server working (Vite needs relaxed rules in dev only).
- Decision (a2): whether admin/manager get a shorter refresh lifetime (backend setting; ask PO).
- Cookie design (b): `Set-Cookie` on login/refresh, cookie-only refresh/logout, CSRF token or Origin check, access token stays in memory. Needs a written design and PO approval before a task is created.

## Acceptance Criteria
- [ ] (a) `vue/no-v-html` enforced and lint passes
- [ ] (a) CSP defined, production build loads and logs in with no CSP violations in the browser console
- [ ] (a) Frontend tests/lint/build pass; QA smoke retest of login/refresh/logout
- [ ] (b) PO decision recorded in the Activity Log (cookie now, Sprint 03, or accept risk)
- [ ] Security retest: VULN-012 status updated (reduced or closed)

## Activity Log
- 2026-10-17 — team_leader: Task created from SECURITY_REPORT.md (VULN-012).
