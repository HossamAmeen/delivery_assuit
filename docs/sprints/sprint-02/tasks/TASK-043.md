# TASK-043: Staging compose must not expose the backend port with NUM_PROXIES=1 (VULN-013)

- **Backlog item:** BL-004 (deploy/infra baseline); security fix for VULN-013 (Medium, blocks staging/production deployment)
- **Assignee:** devops
- **Status:** DONE
- **Depends on:** none (TASK-018 staging compose exists)
- **Estimate:** S
- **Scope recommendation:** **Sprint 02 (fix now, file edit only) and also a hard gate on the DevOps stage.** Reason: a few-line change to `docker/staging/docker-compose.yml` plus a doc note; no code, no local Docker run needed (project rule: no local Docker, so it is verified by review, not by running). No deploy happens in this sprint, but the fix must exist before any staging/production deploy; do not defer past that point.

## Description
`docker/staging/docker-compose.yml:51` publishes gunicorn as `"${BACKEND_PORT:-8000}:8000"` on all interfaces while `NUM_PROXIES=1`. A client can send a forged `X-Forwarded-For` straight to the app and bypass the login (10/min) and registration (30/min) throttles.

## Technical Notes
- Replace the port mapping with `127.0.0.1:8000:8000` or remove `ports:` and use `expose:` / the Docker network only; Nginx (host or container) is the only way in.
- Nginx template: set `X-Forwarded-For` from `$remote_addr` (or confirm exactly one hop with `proxy_add_x_forwarded_for`), do not trust a client-supplied value.
- Document next to VULN-006 (and in the deploy notes): `NUM_PROXIES` must equal the real number of trusted proxy hops; firewall allows only 80/443.
- DevOps does not edit Django code. No Docker commands locally (PO rule).

## Acceptance Criteria
- [ ] Compose no longer publishes the backend on all interfaces
- [ ] Nginx/proxy header handling documented or templated as above
- [ ] Doc note added next to the VULN-006 note
- [ ] Reviewed by Security; at the first staging deploy, retest THR-1/np1 from outside the host (forged header gets 429 after the limit)

## Activity Log
- 2026-10-17 — team_leader: Task created from SECURITY_REPORT.md (VULN-013).
- 2026-10-17 — devops: Implemented (static review only, no Docker run per PO rule). `docker/staging/docker-compose.yml`: backend port now `127.0.0.1:${BACKEND_PORT:-8000}:8000`. Added `docker/staging/nginx-proxy-headers.conf` (`X-Forwarded-For $remote_addr`, overwrite not append). Documented that NUM_PROXIES must equal the real hop count and the firewall allows only 80/443 in `backend/README.md` (Rate limiting section) and `backend/.env.example`. Verified: YAML parses, ports value is loopback. Retest of THR-1/np1 from outside the host is deferred to the first staging deploy. Status IN_REVIEW for Security review.
- 2026-10-17 — qa: Retested, DONE. See QA_REPORT.md section 'Retest: Security fix tasks'. Open items: verified by review only (no Docker run); THR-1/np1 from outside the host and Security review deferred to first staging deploy.
