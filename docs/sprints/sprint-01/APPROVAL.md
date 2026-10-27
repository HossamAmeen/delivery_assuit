# Sprint 01 Approval

## Gate result: SPRINT 01 CLOSED by the PO on 2026-10-11 with E2 left as an open TODO — not deployed
The PO told QA to ignore E2 for now and continue with Sprint 02. E2 stays as the last item in `docs/TODO.md`. Nothing from Sprint 01 is deployed: DevOps/deploy work is paused.
All three required inputs now exist (Backend, QA, Security). The PO accepted E1; QA's sign-off becomes unconditional once E2 (real-device PWA install) passes; E3 is handled as described below. Until then nothing is approved for deployment (`AGENTS.md`: no deploy without an approved `APPROVAL.md`).

## Backend Sign-off
- **Status:** APPROVED
- **Date:** 2026-10-10
- **Tests:** passing (161 backend), coverage 96%, ruff clean, `manage.py check` and `makemigrations --check` clean. Also 49 frontend tests.
- **Migrations:** `apps/users/migrations/0001_initial.py` (custom User)
- **Notes:**
  - Tasks 001–018 and the security fixes 024–026 are DONE. CI tasks 019/020 are DEFERRED by PO decision.
  - Docker (local and staging) was run for real on 2026-10-10; four bugs it exposed (BUG-002..005) are fixed.
  - Known limits: `seed_demo` creates users only (shops, items, orders come with later sprints); brand icons are placeholders; health widget is dev-only (PO decision 2026-10-10).

## QA Sign-off
- **Status:** APPROVED, conditional on E2 passing (E1 accepted by the PO; E3 redefined, see below)
- **Date:** 2026-10-10
- **Open bugs:** none. BUG-001..006 fixed and verified. No Critical/High.
- **Evidence:** 42/42 live API cases, 30/30 real-browser cases, Docker local + staging run (one-command start, Healthy in the browser, data persistence, tests inside containers, Redis/Celery readiness), 161 + 49 tests.
- **Exceptions the PO must accept (or ask to be closed first):**
  - **E1: CI (BL-004, "Should") was never built or tested.** Deferred by PO decision; no automated gate exists yet.
  - **E2: Real PWA install and standalone launch** were not done (Chrome reports no installability errors; needs a phone or desktop Chrome check).
  - **E3: "Fresh clone running from the README alone"**: redefined by the PO decision of 2026-10-11 (no local Docker): QA's strict Docker run (2026-10-10, BUG-006 and three README gaps fixed) stands as the verification, the no-Docker paths were re-verified on clean copies (backend venv, frontend npm), and the Docker start must be re-confirmed once on the server or CI by whoever sets up that environment.

## Security Sign-off
- **Release decision:** PASS (see `SECURITY_REPORT.md`). No open Critical/High/Medium/Low findings. Conditions: `NUM_PROXIES=1` behind Nginx must be confirmed on the real server; TLS redirect and HSTS must be enabled when TLS exists; admin lockout trade-off accepted.

## PO decisions (2026-10-10)
- **E1 accepted:** CI will be built last (TASK-019/020). No CI gate until then.
- **E2** (PWA install on a real device) is closed by a person: see `MANUAL_CHECKS.md`. **E3** is redefined: Docker is not run locally any more; the Docker start is re-confirmed on the server/CI. QA sign-off becomes unconditional when E2 passes.
- **No local Docker** (PO 2026-10-10/11).
- **API docs on staging:** stay off for now; turn on (`API_DOCS_ENABLED=True`) only if staging is not public.
- **Health:** checked server-side only; widget is dev-only.

## Decisions still needed from the PO
1. Run the E2 manual check in `MANUAL_CHECKS.md` (PWA install) and record the result.
2. (Decided: API docs stay off on staging for now.)
3. Brand icons. (Production health-widget question is resolved: PO decided health is checked server-side, widget is dev-only.)
4. When to do CI (TASK-019/020), and DevOps deployment (systemd/Nginx scripts are still TODO).

After acceptance, DevOps can start. Deployment itself (systemd, Nginx, post-deploy health check) is not written yet.
