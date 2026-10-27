// Sprint 03 QA (TASK-054): cookie session in a real headless Chrome against the live backend (no Docker).
// Page and API both on 127.0.0.1 (same site, so SameSite=Strict cookies are sent), as in the task's own check.
// env: BACKEND_DIR, BACKEND_PY, FRONTEND_DIR, PUPPETEER_DIR (dir containing node_modules/puppeteer-core)
import { spawn, spawnSync } from 'node:child_process'
import { createRequire } from 'node:module'
import { mkdtempSync, openSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const { BACKEND_DIR, BACKEND_PY, FRONTEND_DIR, PUPPETEER_DIR } = process.env
const puppeteer = createRequire(PUPPETEER_DIR + '/')('puppeteer-core')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const API_PORT = 8779
const FE_PORT = 5175
const API = `http://127.0.0.1:${API_PORT}/api/v1`
const DEV = `http://127.0.0.1:${FE_PORT}`
const PW = 'Demo!Pass#2468'
const LOGDIR = mkdtempSync(join(tmpdir(), 'qa-cookie-'))
const DB = join(LOGDIR, 'qa.sqlite3')
const env = {
  ...process.env, DATABASE_URL: 'sqlite:///' + DB, HEALTH_CHECK_PASSWORD: 'qa-health-pw', DEBUG: 'False',
  ALLOWED_HOSTS: '127.0.0.1,localhost', SECURE_SSL_REDIRECT: 'False',
  SECRET_KEY: 'qa-secret-key-qa-secret-key-qa-secret-key', DJANGO_SETTINGS_MODULE: 'config.settings.development',
  CORS_ALLOWED_ORIGINS: DEV, RATELIMIT_AUTH: '10000/minute', RATELIMIT_SENSITIVE: '10000/minute',
  RATELIMIT_ANON: '10000/minute', RATELIMIT_USER: '10000/minute',
}
const manage = (args, extra = {}) => spawnSync(BACKEND_PY, ['manage.py', ...args], { cwd: BACKEND_DIR, env: { ...env, ...extra }, encoding: 'utf8' })
const start = (cmd, args, cwd, e, log) => spawn(cmd, args, { cwd, env: e, stdio: ['ignore', openSync(join(LOGDIR, log), 'a'), openSync(join(LOGDIR, log), 'a')], detached: true })
const stop = (p) => { try { process.kill(-p.pid) } catch { /* gone */ } }
async function waitFor(url, accept = (s) => s < 500) {
  for (let i = 0; i < 80; i++) { try { if (accept((await fetch(url)).status)) return } catch { /* not up */ } await sleep(500) }
  throw new Error('timeout ' + url)
}
const results = []
const check = (id, title, ok, note = '') => { results.push({ id, ok }); console.log(`${ok ? 'PASS' : 'FAIL'} ${id} ${title} ${note}`) }
const path = (p) => new URL(p.url()).pathname
const txt = (p, sel) => p.$eval(sel, (e) => e.textContent.trim()).catch(() => null)
async function typeInto(p, sel, v) { await p.$eval(sel, (e) => { e.focus(); e.select() }); await p.keyboard.press('Backspace'); if (v) await p.type(sel, v, { delay: 0 }) }
async function login(p, id, pw = PW) {
  await typeInto(p, '#login-identifier', id); await typeInto(p, '#login-password', pw)
  await p.$eval('button.submit', (e) => e.click())
  await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(200)
}
const state = (p) => p.evaluate(() => ({ ls: Object.fromEntries(Object.entries(localStorage)), ss: Object.fromEntries(Object.entries(sessionStorage)), cookie: document.cookie }))
const doLogout = async (p) => { try { await p.click('[data-testid="user-menu-button"]'); await p.click('[data-testid="logout"]'); return true } catch { return false } }
const TOKEN_RE = /eyJ[A-Za-z0-9_-]{10,}/

if (manage(['migrate', '--noinput']).status !== 0) throw new Error('migrate failed')
if (manage(['seed_demo'], { DEBUG: 'True', DEMO_PASSWORD: PW }).status !== 0) throw new Error('seed failed')
const backend = start(BACKEND_PY, ['manage.py', 'runserver', String(API_PORT), '--noreload'], BACKEND_DIR, env, 'backend.log')
const fe = start('npx', ['vite', '--port', String(FE_PORT), '--strictPort', '--host', '127.0.0.1'], FRONTEND_DIR, { ...process.env, VITE_API_URL: API, VITE_HEALTH_CHECK_TOKEN: 'qa-health-pw' }, 'vite.log')
const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] })
const mk = async (url) => {
  const ctx = await browser.createBrowserContext(); const p = await ctx.newPage()
  p.on('close', () => ctx.close().catch(() => {}))
  p.cap = { net: [], console: [] }
  p.on('response', async (r) => { if (r.url().startsWith(API)) p.cap.net.push({ url: r.url().replace(API, ''), status: r.status(), method: r.request().method(), post: r.request().postData() }) })
  p.on('console', (m) => p.cap.console.push(m.text()))
  await p.setViewport({ width: 360, height: 700 })
  await p.evaluateOnNewDocument(() => { try { if (!localStorage.getItem('locale')) localStorage.setItem('locale', 'en') } catch { /* */ } })
  if (url) await p.goto(DEV + url, { waitUntil: 'networkidle0' })
  return p
}
try {
  await waitFor(`http://127.0.0.1:${API_PORT}/api/v1/health/`, (s) => s === 403 || s === 200)
  await waitFor(DEV + '/')

  // ---- login: no refresh token in JS-reachable places ----
  let p = await mk('/login')
  await login(p, 'demo_client')
  let st = await state(p)
  const cookies = await p.cookies(API + '/auth/')
  const rc = cookies.find((c) => c.name === 'delivery_refresh')
  check('F-LOGIN-1', 'client login lands on /client', path(p) === '/client', path(p))
  check('F-LOGIN-2', 'localStorage has no refresh token and no JWT anywhere in storage', !st.ls['delivery.refresh_token'] && !TOKEN_RE.test(JSON.stringify(st.ls) + JSON.stringify(st.ss)), JSON.stringify(Object.keys(st.ls)))
  check('F-LOGIN-3', 'document.cookie is empty (cookie is HttpOnly)', st.cookie === '', JSON.stringify(st.cookie))
  check('F-LOGIN-4', 'the browser holds delivery_refresh as HttpOnly, SameSite=Strict, Path=/api/v1/auth/', !!rc && rc.httpOnly && rc.sameSite === 'Strict' && rc.path === '/api/v1/auth/', JSON.stringify(rc))
  const loginReq = p.cap.net.find((n) => n.url === '/auth/token/')
  check('F-LOGIN-5', 'login request/response made once and succeeded', loginReq?.status === 200)

  // ---- reload restores via cookie ----
  p.cap.net.length = 0
  await p.reload({ waitUntil: 'networkidle0' })
  const refreshReq = p.cap.net.find((n) => n.url === '/auth/token/refresh/')
  const meReq = p.cap.net.find((n) => n.url === '/auth/me/')
  st = await state(p)
  check('F-RELOAD-1', 'reload keeps the user on /client with the same page', path(p) === '/client' && (await txt(p, 'h1')) === 'Home', path(p))
  check('F-RELOAD-2', 'restore used refresh (200) then /auth/me/ (200)', refreshReq?.status === 200 && meReq?.status === 200, JSON.stringify(p.cap.net.map((n) => [n.url, n.status])))
  check('F-RELOAD-3', 'refresh request body carries no token (empty or {})', !refreshReq?.post || refreshReq.post === '{}', String(refreshReq?.post))
  check('F-RELOAD-4', 'still nothing in storage after restore', !st.ls['delivery.refresh_token'] && st.cookie === '' && Object.keys(st.ss).length === 0)

  // ---- deep link + role guard still work after reload ----
  await p.goto(DEV + '/driver', { waitUntil: 'networkidle0' })
  check('F-GUARD-1', 'client opening /driver is bounced away (role guard intact)', path(p) !== '/driver', path(p))

  // ---- legacy key cleanup ----
  const p2 = await mk('/login')
  await p2.evaluate(() => localStorage.setItem('delivery.refresh_token', 'legacy-old-token'))
  await p2.reload({ waitUntil: 'networkidle0' })
  const leftover = await p2.evaluate(() => localStorage.getItem('delivery.refresh_token'))
  check('F-LEGACY-1', 'old localStorage refresh token is removed at startup', leftover === null, String(leftover))
  const sent = p2.cap.net.filter((n) => (n.post ?? '').includes('legacy-old-token'))
  check('F-LEGACY-2', 'legacy token is never sent to the server', sent.length === 0)
  await p2.close()

  // ---- logout ----
  p.cap.net.length = 0
  await p.goto(DEV + '/client', { waitUntil: 'networkidle0' })
  const clicked = await doLogout(p)
  await p.waitForNetworkIdle({ idleTime: 500 }).catch(() => {}); await sleep(300)
  const outReq = p.cap.net.find((n) => n.url === '/auth/logout/')
  const rcAfter = (await p.cookies(API + '/auth/')).find((c) => c.name === 'delivery_refresh')
  check('F-OUT-1', 'logout control found and clicked', clicked)
  check('F-OUT-2', 'logout goes to /login, API logout 200 with empty body', path(p) === '/login' && outReq?.status === 200 && !outReq?.post, `${path(p)} ${outReq?.status} ${outReq?.post}`)
  check('F-OUT-3', 'cookie is cleared in the browser', !rcAfter, JSON.stringify(rcAfter))
  p.cap.net.length = 0
  await p.reload({ waitUntil: 'networkidle0' })
  const after = p.cap.net.find((n) => n.url === '/auth/token/refresh/')
  check('F-OUT-4', 'after logout a reload does not restore the session (stays /login)', path(p) === '/login', path(p))
  const exp = await txt(p, '.auth-notice')
  check('F-OUT-5', 'no "session expired" error on a plain logged-out visit', !/expired/i.test(exp ?? ''), String(exp))
  await p.close()

  // ---- cold visit with no cookie: no scary message ----
  const p3 = await mk('/login')
  const e3 = await txt(p3, '.auth-notice')
  check('F-COLD-1', 'first visit without a cookie shows no session-expired message', !/expired/i.test(e3 ?? ''), String(e3))
  await p3.close()

  // ---- session ended elsewhere (cookie token blacklisted) ----
  const p4 = await mk('/login')
  await login(p4, 'demo_driver')
  const c4 = (await p4.cookies(API + '/auth/')).find((c) => c.name === 'delivery_refresh')
  await fetch(API + '/auth/logout/', { method: 'POST', headers: { Origin: DEV, Cookie: `delivery_refresh=${c4.value}` } })
  await p4.reload({ waitUntil: 'networkidle0' }); await sleep(300)
  const e4 = await txt(p4, '.auth-notice')
  check('F-ELSE-1', 'session killed elsewhere: reload goes to /login with a session-expired notice', path(p4) === '/login' && /expired/i.test(e4 ?? ''), `${path(p4)} | ${e4}`)
  check('F-ELSE-2', 'no protected content or leftover tokens', !(await state(p4)).ls['delivery.refresh_token'])
  await p4.close()

  // ---- logout works even when the access token is already expired / server rejects ----
  const p5 = await mk('/login')
  await login(p5, 'demo_trader')
  await p5.setRequestInterception(true)
  p5.on('request', (r) => (r.url().endsWith('/auth/logout/') ? r.respond({ status: 500, contentType: 'application/json', body: '{}', headers: { 'Access-Control-Allow-Origin': DEV, 'Access-Control-Allow-Credentials': 'true' } }) : r.continue()))
  const out5 = await doLogout(p5)
  await sleep(1200)
  check('F-OUT-6', 'logout still signs out locally when the logout API fails', out5 && path(p5) === '/login', `${out5} ${path(p5)}`)
  await p5.close()

  // ---- deactivated while signed in ----
  const p6 = await mk('/login')
  await login(p6, 'demo_client')
  manage(['shell', '-c', 'from apps.users.models import User; User.all_objects.filter(username="demo_client").update(status="deactivated")'])
  await p6.reload({ waitUntil: 'networkidle0' }); await sleep(300)
  check('F-STAT-1', 'account deactivated while signed in: reload returns to /login', path(p6) === '/login', path(p6))
  await p6.close()

  // ---- foreign page cannot use the cookie (Origin check seen from a browser) ----
  const evil = await mk(null)
  await evil.goto('http://localhost:' + FE_PORT + '/login', { waitUntil: 'networkidle0' }).catch(() => {})
  const res = await evil.evaluate(async (api) => { try { const r = await fetch(api + '/auth/token/refresh/', { method: 'POST', credentials: 'include' }); return r.status } catch (e) { return 'blocked' } }, API)
  check('F-ORG-1', 'page on a non-allowlisted origin (localhost:5175) cannot refresh via cookie', res === 'blocked' || res === 403 || res === 401, String(res))
  await evil.close()

  const txtLog = (n) => { try { return readFileSync(join(LOGDIR, n), 'utf8') } catch { return '' } }
  check('F-LOG-1', 'no JWT or refresh token written to the vite log', !TOKEN_RE.test(txtLog('vite.log')))
} finally {
  await browser.close().catch(() => {}); stop(backend); stop(fe)
}
const fails = results.filter((r) => !r.ok).length
console.log(`\nPASSED ${results.length - fails}/${results.length}; FAILED: ${fails}`)
process.exit(fails ? 1 : 0)
