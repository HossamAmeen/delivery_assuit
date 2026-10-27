# Sprint 01: manual checks to close E2 and E3

Two short checks that need a person (QA cannot do them). Mark each result at the bottom.

## E2: install the app as a PWA (about 3 minutes)
Needs Chrome on a phone or desktop and a production build served over HTTPS or localhost.

1. `cd frontend && npm ci && npm run build && npm run preview` (opens http://localhost:4173).
   On a phone, use the machine's HTTPS address instead; plain HTTP over the network will not offer installation.
2. Open the page in Chrome. Wait a few seconds, then use the menu: **Install app** / **Add to Home screen**.
3. Open the installed app from the home screen / app launcher.
4. Check:
   - [ ] It opens full-screen with no browser address bar (standalone).
   - [ ] The name is "Delivery" and the icon is the blue placeholder parcel.
   - [ ] The language switcher works and the layout fits the screen (no sideways scrolling).
   - [ ] Switch to Arabic, close and reopen the app: Arabic and RTL are remembered.
   - [ ] Turn on airplane mode and reopen: the app shell still opens (data will not load; that is expected).

## E3: start the system from the README alone (DEFERRED to the server/CI; no local Docker)
**PO decision 2026-10-11:** Docker is not run locally. QA's strict Docker run of 2026-10-10 stands, and the no-Docker setup was re-verified on clean copies. Whoever sets up the server or CI re-confirms the steps below there, once.

QA already did a literal run on 2026-10-10 and fixed the gaps it found (see QA_REPORT.md); this check confirms it works for a newcomer.
Best done by someone who has not seen the project. Needs Docker with Compose. Use a clean clone or copy of the repository.

1. Follow the root `README.md` literally, in order. Do not use any knowledge outside it.
2. Note every place where you had to guess, got an error, or a command was missing.
3. Check:
   - [ ] `docker compose up --build` starts without errors.
   - [ ] http://localhost:5173 opens and shows **Healthy**.
   - [ ] Creating the first admin works as written in step 3.
   - [ ] http://localhost:8000/admin/ lets you log in as that admin and lands on "Site administration".
   - [ ] `docker compose down` then `docker compose up` keeps the admin (data persists).
4. Clean up: `docker compose down -v` deletes the database volume.

## Results (fill in)
| Check | Who | Date | Result | Notes |
|---|---|---|---|---|
| E2 PWA install | | | | |
| E3 README fresh start | | | | |
