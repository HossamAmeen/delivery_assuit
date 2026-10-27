# Delivery Frontend (Vue 3 + Vite + Pinia)

## Setup

```bash
cd frontend
cp .env.example .env      # VITE_API_URL=http://localhost:8000/api/v1
npm install
```

## Run

```bash
npm run dev       # http://localhost:5173
npm run build     # production build in dist/
```

## Test and lint

```bash
npm test          # Vitest, one run (tests/unit/**/*.spec.js)
npm run lint      # ESLint (v-html is forbidden)
npm run format    # Prettier
```

## Structure

`src/{api,components,views,layouts,stores,router,composables,utils,assets}`, `tests/{unit,e2e}`.
Routes: `/` home, and placeholder areas `/driver`, `/trader`, `/client`, `/admin` (Admin and
Manager), each with its own layout, plus a 404 page. Auth guards arrive with SEC-02.

## Languages (English / Arabic)

`vue-i18n` with `src/locales/{en,ar}.json`; English is the default and the choice is saved in
`localStorage`. The language store sets `lang` and `dir` (`rtl` for Arabic) on `<html>`. Rules:
no hard-coded user-facing strings in components (add keys to both JSON files; a test checks they
match), and use CSS logical properties (`margin-inline-start`, `padding-block`, ...), never
`left`/`right`. The Arabic font (Noto Sans Arabic) is self-hosted via `@fontsource`, no CDN.

## PWA (installable app)

`vite-plugin-pwa` (settings in `pwa.config.js`): manifest (standalone, `start_url: /`), icons
192/512/maskable, and a Workbox service worker that precaches the **app shell only**. API
responses are never cached (no runtime caching; `/api/`, `/admin/` are excluded from the
navigation fallback). The service worker is built and registered in production builds only
(`npm run build && npm run preview`), not in `npm run dev`.

- **Updates:** `autoUpdate`. A new version installs in the background and takes over on the next
  load. No update prompt yet.
- **HTTPS:** installation requires HTTPS (localhost is exempt).
- **Icons are placeholders** (`scripts/generate_icons.py`) until brand assets exist (PO to supply).
- **Limitation:** a manifest has one `name`; it is not localized (English). Arabic name would need
  a second manifest, not planned.

## Docker (local)

`Dockerfile` (node 22, `npm ci`, non-root `node` user) runs the Vite dev server on `0.0.0.0:5173`.
Compose (TASK-018) provides the environment. Note the two URLs: `VITE_API_URL` is used by the
**browser**, so it must point at the backend's host-published port (`http://localhost:8000/api/v1`),
not at the container name `backend`. Set `VITE_USE_POLLING=true` if HMR does not see changes on a
bind mount. `.env` is excluded from the image. **Not built or run yet** (PO decision: agents write
Docker files only); validate with `docker build -t delivery-frontend .`. A production (static
serve) stage is not included in Sprint 01.

## Health widget
The home page shows a backend health widget in **development only** (a browser cannot keep the health password secret). In production the health endpoints are checked from the server side (curl, tests, monitoring).
