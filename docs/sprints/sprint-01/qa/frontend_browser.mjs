// QA browser checks for Sprint 01 frontend (TASK-022). Real headless Chrome via puppeteer-core.
// Usage: node frontend_browser.mjs   (env: BACKEND_DIR, BACKEND_PY, FRONTEND_DIR, PUPPETEER_DIR)
import { spawn } from 'node:child_process'
import { createRequire } from 'node:module'

const require = createRequire(process.env.PUPPETEER_DIR + '/')
const puppeteer = require('puppeteer-core')
const { BACKEND_DIR, BACKEND_PY, FRONTEND_DIR } = process.env
const HPW = 'qa-health-pw'
const API = 'http://127.0.0.1:8777/api/v1'
const results = []
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const check = (id, title, ok, note = '') => {
  results.push({ id, ok })
  console.log(`${ok ? 'PASS' : 'FAIL'} ${id} ${title} ${note}`)
}

function start(cmd, args, cwd, env) {
  return spawn(cmd, args, { cwd, env: { ...process.env, ...env }, stdio: 'ignore', detached: true })
}
const stop = (p) => { try { process.kill(-p.pid) } catch { /* already gone */ } }
async function waitFor(url, accept = (s) => s < 500) {
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(url); if (accept(r.status)) return } catch { /* not up */ }
    await sleep(500)
  }
  throw new Error('timeout ' + url)
}

const backendEnv = { DATABASE_URL: 'sqlite:///' + process.env.QA_DB + '', HEALTH_CHECK_PASSWORD: HPW, DEBUG: 'True', SECRET_KEY: 'qa-secret-key-qa-secret-key-qa-secret-key', DJANGO_SETTINGS_MODULE: 'config.settings.development', CORS_ALLOWED_ORIGINS: 'http://localhost:5174,http://localhost:4174' }
let backend = start(BACKEND_PY, ['manage.py', 'runserver', '8777', '--noreload'], BACKEND_DIR, backendEnv)
const viteEnv = { VITE_API_URL: API, VITE_HEALTH_CHECK_TOKEN: HPW }
const dev = start('npx', ['vite', '--port', '5174', '--strictPort', '--host', 'localhost'], FRONTEND_DIR, viteEnv)
const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] })

try {
  await waitFor('http://127.0.0.1:8777/api/v1/health/', (s) => s === 403 || s === 200)
  await waitFor('http://localhost:5174/')
  const DEV = 'http://localhost:5174'

  const open = async (url, { w = 360, h = 640, lang = 'en' } = {}) => {
    const ctx = await browser.createBrowserContext() // isolated storage per page
    const page = await ctx.newPage()
    page.on('close', () => ctx.close().catch(() => {}))
    await page.setViewport({ width: w, height: h })
    await page.evaluateOnNewDocument((l) => { try { if (!localStorage.getItem('locale')) localStorage.setItem('locale', l) } catch { /* */ } }, lang)
    await page.goto(url, { waitUntil: 'networkidle0' })
    return page
  }
  const text = (page, sel) => page.$eval(sel, (e) => e.textContent.trim())

  // BL-002: home, areas, health
  let p = await open(DEV + '/')
  check('BL002-1', 'dev server renders home page (title + health)', (await text(p, 'h1')) === 'Delivery' && (await text(p, '[data-testid="health-status"]')) === 'Healthy')
  const links = await p.$$eval('nav[aria-label="Areas"] a', (as) => as.map((a) => a.getAttribute('href')))
  check('BL002-2', 'home links to the four areas', JSON.stringify(links) === JSON.stringify(['/driver', '/trader', '/client', '/admin']))
  const titles = []
  for (const a of ['driver', 'trader', 'client', 'admin']) {
    await p.goto(`${DEV}/${a}`, { waitUntil: 'networkidle0' })
    titles.push([a, await p.$eval(`[data-testid="layout-${a}"] h1`, (e) => e.textContent.trim()), await p.$$eval('[data-testid^="layout-"]', (e) => e.length)])
  }
  check('BL002-3', 'each area route renders its own distinct layout', new Set(titles.map((t) => t[1])).size === 4 && titles.every((t) => t[2] === 1), JSON.stringify(titles.map((t) => t[1])))
  await p.goto(DEV + '/no/such/page', { waitUntil: 'networkidle0' })
  check('BL002-4', 'unknown route shows 404 page', (await text(p, 'h1')) === 'Page not found')
  const apiCalls = []
  p.on('request', (r) => r.url().includes('/health/') && apiCalls.push(r.url()))
  await p.goto(DEV + '/', { waitUntil: 'networkidle0' })
  check('BL002-5', 'health call goes to base URL from env (no hardcoded URL)', apiCalls.some((u) => u.startsWith(API)), apiCalls[0] ?? '')
  await p.close()

  // Failure state: backend stopped
  stop(backend); await sleep(1500)
  p = await open(DEV + '/')
  const netEn = await text(p, '[role="alert"]')
  check('BL002-6', 'backend down -> friendly error + Retry (en)', netEn.includes('Cannot reach the server') && !!(await p.$('[role="alert"] button')), netEn)
  await p.click('.language-switcher [data-locale="ar"]'); await sleep(300)
  const netAr = await text(p, '[role="alert"]')
  check('BL006-1', 'network error fallback is localized (ar)', netAr.includes('تعذر الوصول'), netAr)
  await p.close()
  backend = start(BACKEND_PY, ['manage.py', 'runserver', '8777', '--noreload'], BACKEND_DIR, backendEnv)
  await waitFor('http://127.0.0.1:8777/api/v1/health/', (s) => s === 403 || s === 200)

  // Retry after recovery
  p = await open(DEV + '/')
  check('BL002-7', 'backend back up -> Healthy again', (await text(p, '[data-testid="health-status"]')) === 'Healthy')
  await p.close()

  // BL-006: languages on all screens, persistence, no overflow
  for (const route of ['/', '/driver', '/trader', '/client', '/admin', '/nope']) {
    for (const [w, h] of [[360, 640], [1280, 800]]) {
      p = await open(DEV + route, { w, h })
      const en = await p.evaluate(() => ({ dir: document.documentElement.dir, lang: document.documentElement.lang, h1: document.querySelector('h1').textContent, ov: document.documentElement.scrollWidth - document.documentElement.clientWidth }))
      await p.click('.language-switcher [data-locale="ar"]'); await sleep(200)
      const ar = await p.evaluate(() => ({ dir: document.documentElement.dir, lang: document.documentElement.lang, h1: document.querySelector('h1').textContent, ov: document.documentElement.scrollWidth - document.documentElement.clientWidth, font: getComputedStyle(document.body).fontFamily }))
      await p.reload({ waitUntil: 'networkidle0' })
      const after = await p.evaluate(() => ({ dir: document.documentElement.dir, h1: document.querySelector('h1').textContent }))
      const ok = en.dir === 'ltr' && en.lang === 'en' && ar.dir === 'rtl' && ar.lang === 'ar' && en.h1 !== ar.h1 && en.ov <= 0 && ar.ov <= 0 && after.dir === 'rtl' && after.h1 === ar.h1
      check(`BL006-2 ${route} ${w}px`, 'switch en<->ar flips text+dir, persists on reload, no overflow', ok, JSON.stringify({ en: en.h1, ar: ar.h1, ov: [en.ov, ar.ov] }))
      await p.close()
    }
  }

  // Server error message language follows UI (wrong token -> 403 message)
  const bad = start('npx', ['vite', '--port', '5175', '--strictPort', '--host', 'localhost'], FRONTEND_DIR, { ...viteEnv, VITE_HEALTH_CHECK_TOKEN: 'wrong' })
  try {
    await waitFor('http://localhost:5175/')
    // backend CORS needs this origin too
    stop(backend); await sleep(800)
    backend = start(BACKEND_PY, ['manage.py', 'runserver', '8777', '--noreload'], BACKEND_DIR, { ...backendEnv, CORS_ALLOWED_ORIGINS: 'http://localhost:5175' })
    await waitFor('http://127.0.0.1:8777/api/v1/health/', (s) => s === 403 || s === 200)
    p = await open('http://localhost:5175/')
    const en = await text(p, '[role="alert"]')
    await p.click('.language-switcher [data-locale="ar"]'); await sleep(800)
    const ar = await text(p, '[role="alert"]')
    await p.click('.language-switcher [data-locale="en"]'); await sleep(800)
    const en2 = await text(p, '[role="alert"]')
    check('BL006-3', 'server error message language follows UI language (live backend)', en.includes('Invalid health check password.') && ar.includes('كلمة مرور فحص الحالة غير صالحة.') && en2.includes('Invalid health check password.'), `${en} | ${ar}`)
    await p.close()
  } finally { stop(bad) }
  stop(backend); await sleep(800)
  backend = start(BACKEND_PY, ['manage.py', 'runserver', '8777', '--noreload'], BACKEND_DIR, backendEnv)
  await waitFor('http://127.0.0.1:8777/api/v1/health/', (s) => s === 403 || s === 200)

  // Keyboard + accessibility basics
  p = await open(DEV + '/')
  const order = []
  for (let i = 0; i < 9; i++) {
    await p.keyboard.press('Tab')
    order.push(await p.evaluate(() => { const e = document.activeElement; const cs = getComputedStyle(e); return [e.className.split(' ')[0] || e.tagName, e.textContent.trim().slice(0, 12), cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) >= 2] }))
  }
  check('A11Y-1', 'keyboard Tab reaches skip link, switcher, links, nav in order with visible focus', order[0][0] === 'skip-link' && order.slice(0, 9).every((o) => o[2]) && order.some((o) => o[1] === 'English') && order.some((o) => o[1] === 'Driver'), JSON.stringify(order.map((o) => o[1])))
  const lm = await p.evaluate(() => ({ header: !!document.querySelector('header'), main: document.querySelectorAll('main').length, nav: [...document.querySelectorAll('nav')].every((n) => n.getAttribute('aria-label')), h1: document.querySelectorAll('h1').length, htmlLang: document.documentElement.lang }))
  check('A11Y-2', 'landmarks: header, one main, labelled navs, one h1, html lang', lm.header && lm.main === 1 && lm.nav && lm.h1 === 1 && !!lm.htmlLang, JSON.stringify(lm))
  const small = await p.evaluate(() => [...document.querySelectorAll('a,button')].filter((e) => { const b = e.getBoundingClientRect(); return b.width && (b.width < 43.5 || b.height < 43.5) && !e.classList.contains('skip-link') }).map((e) => e.textContent.trim()))
  check('A11Y-3', 'touch targets >= 44px at 360px', small.length === 0, small.join(','))
  await p.close()
  stop(dev)

  // PWA: production build over localhost
  const prev = start('npx', ['vite', 'preview', '--port', '4174', '--strictPort', '--host', 'localhost'], FRONTEND_DIR, {})
  try {
    await waitFor('http://localhost:4174/')
    p = await browser.newPage() // default (non-incognito) context: needed for installability
    await p.setViewport({ width: 360, height: 640 })
    await p.goto('http://localhost:4174/', { waitUntil: 'networkidle0' })
    const sw = await p.evaluate(async () => { const r = await navigator.serviceWorker.ready; return { scope: r.scope, state: r.active?.state } })
    check('BL005-1', 'service worker registers and activates (prod build, localhost)', sw.state === 'activated', JSON.stringify(sw))
    const cdp = await p.createCDPSession()
    await cdp.send('Page.enable')
    const inst = await cdp.send('Page.getInstallabilityErrors')
    check('BL005-2', 'Chrome reports no installability errors', inst.installabilityErrors.length === 0, JSON.stringify(inst.installabilityErrors))
    const man = await cdp.send('Page.getAppManifest')
    const m = JSON.parse(man.data || '{}')
    check('BL005-3', 'manifest: name, standalone, icons incl. maskable', m.name === 'Delivery' && m.display === 'standalone' && m.icons.some((i) => i.purpose === 'maskable') && m.icons.some((i) => i.sizes === '192x192') && m.icons.some((i) => i.sizes === '512x512') && (man.errors || []).length === 0, JSON.stringify(man.errors || []))
    const iconOk = await p.evaluate(async () => (await Promise.all(['/icons/icon-192.png', '/icons/icon-512.png', '/icons/icon-maskable-512.png'].map((u) => fetch(u).then((r) => r.status)))).every((s) => s === 200))
    check('BL005-4', 'icon files load', iconOk)
    // service worker must not cache API responses
    await p.evaluate(async (api) => { await fetch(api + '/health/', { headers: { 'X-Health-Check-Token': 'x' } }).catch(() => {}) }, API)
    await sleep(500)
    const cached = await p.evaluate(async () => { const out = []; for (const n of await caches.keys()) { const c = await caches.open(n); out.push(...(await c.keys()).map((r) => r.url)) } return out })
    check('BL005-5', 'service worker caches app shell only, never /api/', cached.length > 5 && !cached.some((u) => u.includes('/api/') || u.includes('8777')), `${cached.length} entries`)
    // offline: shell loads
    await p.setOfflineMode(true)
    await p.reload({ waitUntil: 'domcontentloaded' }).catch(() => {})
    await sleep(800)
    const offline = await p.evaluate(() => document.querySelector('h1')?.textContent ?? '')
    check('BL005-6', 'app shell opens offline (installability only; API still fails gracefully)', offline === 'Delivery', offline)
    await p.setOfflineMode(false)
    await p.close()
  } finally { stop(prev) }
} finally {
  await browser.close(); stop(dev); stop(backend)
}
const fails = results.filter((r) => !r.ok)
console.log(`\n${results.length - fails.length}/${results.length} passed`)
process.exit(fails.length ? 1 : 0)
