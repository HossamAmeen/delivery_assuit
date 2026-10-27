// Sprint 02 axe run over every new screen (en/ar x 360/1280), signed in per role where needed.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { DEV, setupDb, startBackend, startFrontend, stop, waitFor, launch, open, login, sleep } from './frontend_lib.mjs'
const axe = readFileSync(join(process.env.AXE_DIR, 'node_modules/axe-core/axe.min.js'), 'utf8')
setupDb(); const backend = startBackend(); const fe = startFrontend(); const b = await launch()
let total = 0, runs = 0
try {
  await waitFor('http://127.0.0.1:8778/api/v1/health/', (s) => s === 403 || s === 200); await waitFor(DEV + '/')
  const screens = [['/login', null], ['/register', null], ['/register/client', null], ['/register/driver', null], ['/register/trader', null], ['/driver', 'demo_driver'], ['/trader', 'demo_trader'], ['/client', 'demo_client'], ['/admin', 'demo_admin'], ['/nope', null], ['login-error', null], ['login-validation', null], ['register-validation', null], ['pending', null], ['menu-open', 'demo_client']]
  for (const lang of ['en', 'ar']) for (const [route, user] of screens) for (const w of [360, 1280]) {
    const p = await open(b, route.startsWith('/') && !user ? route : '/login', { w, h: 800, lang })
    if (user) { await login(p, user) }
    if (route === 'login-error') { await login(p, 'demo_driver_pending') }
    if (route === 'login-validation') { await p.$eval('button.submit', (e) => e.click()); await sleep(200) }
    if (route === 'register-validation') { await p.goto(DEV + '/register/driver', { waitUntil: 'networkidle0' }); await p.$eval('button.submit', (e) => e.click()); await sleep(200) }
    if (route === 'pending') { await p.goto(DEV + '/register/driver', { waitUntil: 'networkidle0' }); await p.type('#reg-full_name', 'Axe Driver'); await p.type('#reg-phone', '010' + String(Math.floor(Math.random() * 1e8)).padStart(8, '0')); await p.type('#reg-password', 'Zx9!kLm#Qw27pR'); await p.type('#reg-confirm', 'Zx9!kLm#Qw27pR'); await p.$eval('button.submit', (e) => e.click()); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(300) }
    if (route === 'menu-open') { await p.click('[data-testid="user-menu-button"]'); await sleep(200) }
    await p.evaluate(axe)
    const r = await p.evaluate(() => axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] }))
    runs++
    for (const v of r.violations) { total++; console.log(lang, route, w, v.id, v.impact, v.nodes.length, v.nodes[0].html.slice(0, 100).replace(/\n/g, ' ')) }
    const f = await p.evaluate(() => document.fonts.check('16px "Noto Sans Arabic"'))
    if (lang === 'ar' && !f) console.log('ARABIC FONT NOT LOADED', route)
    await p.close()
  }
} finally { await b.close(); stop(fe); stop(backend) }
console.log(`axe runs: ${runs}; violations total: ${total}`)
process.exit(total ? 1 : 0)
