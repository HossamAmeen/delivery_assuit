# TASK-026: Hardening: JSON-only renderer, placeholder-secret guard, staging notes

- **Backlog item:** BL-001 (security fix)
- **Assignee:** backend
- **Status:** DONE
- **Depends on:** TASK-024
- **Estimate:** S

## Description
VULN-004 (Low): HTML/browsable API renderer enabled. VULN-005 (Low, QA BUG-001): placeholder or short secrets accepted outside development. VULN-006 (Low): staging TLS defaults. VULN-010 (Info): `# nosec B310` on the healthcheck script.

## Technical Notes
- `DEFAULT_RENDERER_CLASSES` = JSON only (docs endpoints unaffected).
- Production/staging fail at startup for `SECRET_KEY`/`HEALTH_CHECK_PASSWORD` equal to `change-me` or shorter than 32 (SECRET_KEY).
- README note for staging TLS flags.

## Acceptance Criteria
- [x] `Accept: text/html` on an API endpoint returns JSON
- [x] Production/staging refuse placeholder secrets; development unaffected
- [x] Tests written and passing; ruff clean

## Activity Log
- 2026-10-10 — team_leader: Task created from SECURITY_REPORT.md (VULN-004/005/006/010) and QA BUG-001.
- 2026-10-10 — backend: DEFAULT_RENDERER_CLASSES = JSON only (text/html-only Accept -> JSON 406, ?format=api -> 404; docs still work); config/settings/secrets.py validate_secrets() called from production.py (staging inherits): SECRET_KEY < 32 chars or any placeholder (change-me, insecure, ...) and placeholder HEALTH_CHECK_PASSWORD stop startup, development unaffected; nosec B310 on healthcheck.py; README note on staging TLS flags. 18 new tests (settings modules imported in subprocesses). Full suite 158 passing (before the final test tightening; hardening file re-run), ruff clean. Needs Security retest. Status IN_REVIEW.
- 2026-10-10 — security/qa: retested live, VERIFIED (SECURITY_REPORT.md Retest). Full suite 159 passing, coverage 96%. Status DONE.
