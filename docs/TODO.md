# TODO (reminders from PO, 2026-10-08)

- [ ] **CI**: GitHub Actions pipeline (TASK-019 backend job, TASK-020 frontend job; BL-004). PO decision 2026-10-10: do this at the END (after the other Sprint 01 decisions and deploy work).
- [ ] **Deploy**: systemd-based deployment (deploy scripts, systemd template, Nginx template, post-deploy health check). Deferred; DevOps stage after sprint approval.
- [ ] **Celery + Redis**: enabled on staging/server only; dev settings keep them off. Verify on staging.
- [x] Run/validate Docker files: done 2026-10-10 (local and staging stacks), 4 bugs fixed.
- [ ] BL-007: seed orders/shops/items once those models exist.
- [ ] PWA icons are placeholders until brand assets exist.
- [x] `VITE_HEALTH_CHECK_TOKEN`: resolved 2026-10-10. The widget is dev-only; production health is checked with curl/tests/monitoring. The token never reaches a production bundle.
- [x] Staging compose written (TASK-018) and run once 2026-10-10.
- [x] Verify real Redis/Celery readiness checks against a live broker: done 2026-10-10 (staging compose, redis ok, celery ok).
- [ ] Decide API docs in staging (currently off: N-8).
- [ ] Production health monitoring from the server side: deploy script curl check (DevOps) and Sentry (or similar) when deployment work starts.
- [ ] **LAST STEP: Sprint 01 PWA install check (E2).** On a phone or Chrome: `cd frontend && npm run build && npm run preview`, open the link, install the app ("Install app" / "Add to Home screen"), open it and check: full screen, name "Delivery", Arabic/English both work. Steps: `docs/sprints/sprint-01/MANUAL_CHECKS.md`. Then tell Claude the result so QA sign-off becomes unconditional.

## Sprint 02 security triage (2026-10-17, Team Leader)
- [x] TASK-041 (VULN-011) and TASK-043 (VULN-013): DONE 2026-10-17 (QA retest passed; Security: fixed with conditions). Conditions remain: PostgreSQL concurrency run (E1) and VULN-013 outside-host retest at first staging deploy (E2). **VULN-013 conditions must be checked before any staging/production deploy.**
- [ ] TASK-042 (VULN-012): moved to Sprint 03. PO choice 2026-10-26 is the HttpOnly refresh cookie. TASK-044, TASK-045 and TASK-054 are DONE for QA (2026-10-27). Not closed until the Security retest. BUG-010 (Low) is open.
- [ ] Deferred Low/Info candidates, no tasks yet: VULN-014 (500 on bad input; Nginx body limit), VULN-015 (login max_length), VULN-016 (identifier normalisation), VULN-017 (reuse detection, revoke on password change; with Sprint 03 recovery), VULN-018 (verify phone/email, unique email; Sprint 03), VULN-019 (Cache-Control no-store on auth), VULN-020/021/022 (Info). Details in docs/sprints/sprint-02/SPRINT.md.
