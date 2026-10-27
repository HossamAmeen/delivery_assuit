// Shared helpers for Sprint 02 frontend QA (TASK-040). No Docker: venv backend + vite dev + headless Chrome.
// env: BACKEND_DIR, BACKEND_PY, FRONTEND_DIR, PUPPETEER_DIR (dir containing node_modules/puppeteer-core), AXE_DIR (optional)
import { spawn, spawnSync } from 'node:child_process'
import { createRequire } from 'node:module'
import { mkdtempSync, openSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

export const { BACKEND_DIR, BACKEND_PY, FRONTEND_DIR, PUPPETEER_DIR } = process.env
const require = createRequire(PUPPETEER_DIR + '/')
export const puppeteer = require('puppeteer-core')
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
export const API_PORT = 8778
export const FE_PORT = 5174
export const API = `http://127.0.0.1:${API_PORT}/api/v1`
export const DEV = `http://localhost:${FE_PORT}`
export const DEMO_PW = 'Demo!Pass#2468'
export const STRONG = 'Zx9!kLm#Qw27pR'
export const LOGDIR = mkdtempSync(join(tmpdir(), 'qa-fe-'))
export const DB = join(LOGDIR, 'qa.sqlite3')

export const backendEnv = (extra = {}) => ({
  ...process.env, DATABASE_URL: 'sqlite:///' + DB, HEALTH_CHECK_PASSWORD: 'qa-health-pw', DEBUG: 'False',
  ALLOWED_HOSTS: '127.0.0.1,localhost', SECURE_SSL_REDIRECT: 'False',
  SECRET_KEY: 'qa-secret-key-qa-secret-key-qa-secret-key', DJANGO_SETTINGS_MODULE: 'config.settings.development',
  CORS_ALLOWED_ORIGINS: DEV, RATELIMIT_AUTH: '10000/minute', RATELIMIT_SENSITIVE: '10000/minute',
  RATELIMIT_ANON: '10000/minute', RATELIMIT_USER: '10000/minute', ...extra,
})
export const manage = (args, extra = {}) =>
  spawnSync(BACKEND_PY, ['manage.py', ...args], { cwd: BACKEND_DIR, env: backendEnv(extra), encoding: 'utf8' })

export function start(cmd, args, cwd, env, logName) {
  const fd = openSync(join(LOGDIR, logName), 'a')
  return spawn(cmd, args, { cwd, env, stdio: ['ignore', fd, fd], detached: true })
}
export const stop = (p) => { try { process.kill(-p.pid) } catch { /* gone */ } }
export const readLog = (n) => { try { return readFileSync(join(LOGDIR, n), 'utf8') } catch { return '' } }
export async function waitFor(url, accept = (s) => s < 500) {
  for (let i = 0; i < 80; i++) {
    try { const r = await fetch(url); if (accept(r.status)) return } catch { /* not up */ }
    await sleep(500)
  }
  throw new Error('timeout ' + url)
}
export const startBackend = (extra = {}) => start(BACKEND_PY, ['manage.py', 'runserver', String(API_PORT), '--noreload'], BACKEND_DIR, backendEnv(extra), 'backend.log')
export const startFrontend = () => start('npx', ['vite', '--port', String(FE_PORT), '--strictPort', '--host', 'localhost'], FRONTEND_DIR, { ...process.env, VITE_API_URL: API, VITE_HEALTH_CHECK_TOKEN: 'qa-health-pw' }, 'vite.log')

export function setupDb() {
  const m = manage(['migrate', '--noinput'])
  if (m.status !== 0) throw new Error('migrate failed ' + m.stderr)
  const s = manage(['seed_demo'], { DEBUG: 'True', DEMO_PASSWORD: DEMO_PW })
  if (s.status !== 0) throw new Error('seed failed ' + s.stderr)
}
export const setStatus = (phone, status) => manage(['shell', '-c',
  `from apps.users.models import User; User.all_objects.filter(phone="${phone}").update(status="${status}")`])

export const launch = () => puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] })

// Isolated context+page with console/request capture.
export async function open(browser, path, { w = 360, h = 700, lang = 'en', cap = {} } = {}) {
  const ctx = await browser.createBrowserContext()
  const page = await ctx.newPage()
  page.on('close', () => ctx.close().catch(() => {}))
  page.cap = { console: [], urls: [], navs: [], ...cap }
  page.on('console', (m) => page.cap.console.push(m.text()))
  page.on('pageerror', (e) => page.cap.console.push('PAGEERROR ' + e.message))
  page.on('request', (r) => page.cap.urls.push(r.url()))
  page.on('framenavigated', (f) => { if (f === page.mainFrame()) page.cap.navs.push(f.url()) })
  await page.setViewport({ width: w, height: h })
  await page.evaluateOnNewDocument((l) => { try { if (!localStorage.getItem('locale')) localStorage.setItem('locale', l) } catch { /* */ } }, lang)
  if (path) await page.goto(DEV + path, { waitUntil: 'networkidle0' })
  return page
}
export const path = (page) => new URL(page.url()).pathname + new URL(page.url()).search
export const txt = (page, sel) => page.$eval(sel, (e) => e.textContent.trim()).catch(() => null)
export async function typeInto(page, sel, value) {
  await page.$eval(sel, (e) => { e.focus(); e.select() }); await page.keyboard.press('Backspace')
  if (value) await page.type(sel, value, { delay: 0 })
}
export async function login(page, id, pw = DEMO_PW) {
  await typeInto(page, '#login-identifier', id)
  await typeInto(page, '#login-password', pw)
  await page.$eval('button.submit', (e) => e.click())
  await page.waitForNetworkIdle({ idleTime: 400 }).catch(() => {})
  await sleep(200)
}
export const authKeys = (page) => page.evaluate(() => ({ ls: Object.fromEntries(Object.entries(localStorage)), ss: Object.fromEntries(Object.entries(sessionStorage)), cookie: document.cookie }))
