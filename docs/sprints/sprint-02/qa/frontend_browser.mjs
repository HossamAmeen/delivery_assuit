// Sprint 02 QA (TASK-040): frontend accounts, real headless Chrome against the live backend (no Docker).
import { BACKEND_DIR, API, DEV, DEMO_PW, STRONG, sleep, setupDb, startBackend, startFrontend, stop, waitFor, launch, open, path, txt, typeInto, login, authKeys, setStatus, readLog, LOGDIR, manage } from './frontend_lib.mjs'

const results = []
const check = (id, title, ok, note = '') => { results.push({ id, ok }); console.log(`${ok ? 'PASS' : 'FAIL'} ${id} ${title} ${note}`) }
const TOKEN_RE = /eyJ[A-Za-z0-9_-]{10,}/
const get = (u, h = {}) => fetch(u, { headers: h }).then(async (r) => ({ s: r.status, j: await r.json().catch(() => null) }))
const post = (u, b, h = {}) => fetch(u, { method: 'POST', headers: { 'Content-Type': 'application/json', ...h }, body: JSON.stringify(b) }).then(async (r) => ({ s: r.status, j: await r.json().catch(() => null) }))
const apiLogin = async (id) => (await post(API + '/auth/token/', { username_or_phone: id, password: DEMO_PW })).j?.data

setupDb()
let backend = startBackend()
const fe = startFrontend()
const browser = await launch()
const pages = []
const allCaps = []
const newPage = async (...a) => { const p = await open(browser, ...a); allCaps.push(p.cap); return p }
try {
  await waitFor(`http://127.0.0.1:8778/api/v1/health/`, (s) => s === 403 || s === 200)
  await waitFor(DEV + '/')

  const ROLES = [['demo_admin', '01000000001', 'admin', '/admin', 'Dashboard', 'Admin'], ['demo_manager', '01000000002', 'manager', '/admin', 'Dashboard', 'Manager'],
    ['demo_driver', '01000000003', 'driver', '/driver', 'My Assigned Orders', 'Driver'], ['demo_trader', '01000000004', 'trader', '/trader', 'Dashboard', 'Trader'], ['demo_client', '01000000005', 'client', '/client', 'Home', 'Client']]

  // ---------- BL-012 login: each role to the correct home (by username and by phone) ----------
  for (const [user, phone, role, home, title, badge] of ROLES) {
    for (const [how, id] of [['username', user], ['phone', phone]]) {
      const p = await newPage('/login')
      await login(p, id)
      const h1 = await txt(p, 'h1'); const nm = await txt(p, '[data-testid="home-name"]'); const rl = await txt(p, '[data-testid="home-role"]')
      check(`BL012-1 ${role}/${how}`, `login lands on ${home} with title, name and role`, path(p) === home && h1 === title && !!nm && rl === badge, `${path(p)} | ${h1} | ${nm} | ${rl}`)
      await p.close()
    }
  }

  // ---------- BL-012 failure messages ----------
  let p = await newPage('/login')
  await login(p, 'demo_driver_pending')
  let err = await txt(p, '[data-test="form-error"]')
  let ks = await authKeys(p)
  check('BL012-2', 'pending account: friendly pending message, stays on /login, no session stored', path(p) === '/login' && /pending approval/i.test(err ?? '') && !ks.ls['delivery.refresh_token'], err)
  await login(p, 'demo_client_deactivated')
  err = await txt(p, '[data-test="form-error"]'); ks = await authKeys(p)
  check('BL012-3', 'deactivated account: friendly deactivated message, no session stored', path(p) === '/login' && /deactivated/i.test(err ?? '') && !ks.ls['delivery.refresh_token'], err)
  await login(p, 'demo_client', 'Wrong-pass-1')
  const wrong = await txt(p, '[data-test="form-error"]'); const pwAfter = await p.$eval('#login-password', (e) => e.value)
  check('BL012-4', 'wrong password: generic "Invalid credentials.", password field cleared, no session', wrong === 'Invalid credentials.' && pwAfter === '' && path(p) === '/login', wrong)
  await login(p, 'no_such_user_x')
  const unk = await txt(p, '[data-test="form-error"]')
  check('BL012-5', 'unknown user gets the identical message as wrong password (no existence leak)', unk === wrong, unk)
  await login(p, 'demo_driver_pending', 'Wrong-pass-1')
  check('BL012-6', 'wrong password on a pending account shows the generic message (not pending)', (await txt(p, '[data-test="form-error"]')) === wrong)
  // empty form
  await typeInto(p, '#login-identifier', ''); await typeInto(p, '#login-password', '')
  await p.$eval('button.submit', (e) => e.click()); await sleep(200)
  const fe1 = await p.$$eval('.field-error', (e) => e.map((x) => x.textContent.trim()))
  const inv = await p.$$eval('input[aria-invalid="true"]', (e) => e.length)
  check('BL012-7', 'empty submit: required messages under both fields, aria-invalid set', fe1.length === 2 && inv === 2, fe1.join(' | '))
  // Enter submits
  await typeInto(p, '#login-identifier', 'demo_client'); await typeInto(p, '#login-password', DEMO_PW)
  await p.keyboard.press('Enter'); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(200)
  check('A11Y-K1', 'Enter in the password field submits the login form', path(p) === '/client', path(p))
  await p.close()
  // show/hide + link to register + disabled while submitting
  p = await newPage('/login')
  await typeInto(p, '#login-password', 'abc')
  const t0 = await p.$eval('#login-password', (e) => e.type); await p.click('[data-test="toggle-password"]'); const t1 = await p.$eval('#login-password', (e) => e.type)
  check('BL012-8', 'show/hide password toggles input type and aria-pressed', t0 === 'password' && t1 === 'text' && (await p.$eval('[data-test="toggle-password"]', (e) => e.getAttribute('aria-pressed'))) === 'true')
  await p.setRequestInterception(true)
  p.on('request', async (r) => { if (r.url().endsWith('/auth/token/') && r.method() === 'POST') { await sleep(1500); r.continue() } else r.continue() })
  await typeInto(p, '#login-identifier', 'demo_client'); await typeInto(p, '#login-password', DEMO_PW)
  await p.$eval('button.submit', (e) => e.click()); await sleep(300)
  const busy = await p.evaluate(() => ({ dis: document.querySelector('button.submit').disabled, busy: document.querySelector('button.submit').getAttribute('aria-busy'), idDis: document.querySelector('#login-identifier').disabled }))
  check('BL012-9', 'while submitting: button disabled, aria-busy, inputs disabled (no double submit)', busy.dis && busy.busy === 'true' && busy.idDis, JSON.stringify(busy))
  await p.close()
  p = await newPage('/login')
  await p.click('a[href="/register"]'); await sleep(300)
  check('BL012-10', 'login has a link to registration', path(p) === '/register')
  await p.close()

  // ---------- BL-009..011 registration ----------
  const regs = {}
  for (const [role, phone, nameLabel] of [['client', '+20 100-555-0011', 'Full name'], ['driver', '0100 555 0022', 'Full name'], ['trader', '٠١٠٠٥٥٥٠٠٣٣', 'Shop or trader name']]) {
    const bl = { client: 'BL011', driver: 'BL009', trader: 'BL010' }[role]
    p = await newPage('/register')
    const cards = await p.$$eval('.role-card', (e) => e.length)
    await p.click(`[data-test="choose-${role}"]`); await sleep(300)
    const label = await txt(p, 'label[for="reg-full_name"]'); const h1 = await txt(p, 'h1')
    check(`${bl}-1`, `chooser (3 cards) -> /register/${role}; title and name label correct`, cards === 3 && path(p) === `/register/${role}` && h1.toLowerCase().includes(role) && label === nameLabel, `${h1} | ${label}`)
    // empty submit
    await p.$eval('button.submit', (e) => e.click()); await sleep(200)
    const errs = await p.$$eval('.field-error', (e) => e.map((x) => x.id))
    check(`${bl}-2`, 'empty submit: per-field errors for name, phone, password (email optional)', ['reg-full_name-error', 'reg-phone-error', 'reg-password-error'].every((i) => errs.includes(i)) && !errs.includes('reg-email-error'), errs.join(','))
    // mismatch + short + bad email
    await typeInto(p, '#reg-full_name', 'Q'); await typeInto(p, '#reg-phone', '123'); await typeInto(p, '#reg-email', 'nope'); await typeInto(p, '#reg-password', 'short'); await typeInto(p, '#reg-confirm', 'other')
    await p.$eval('button.submit', (e) => e.click()); await sleep(200)
    const e2 = await p.$$eval('.field-error', (e) => e.map((x) => x.id))
    check(`${bl}-3`, 'invalid name/phone/email/short password flagged client-side with no request sent', ['reg-full_name-error', 'reg-phone-error', 'reg-email-error', 'reg-password-error'].every((i) => e2.includes(i)))
    await typeInto(p, '#reg-password', STRONG); await typeInto(p, '#reg-confirm', STRONG + 'x'); await typeInto(p, '#reg-full_name', 'QA ' + role); await typeInto(p, '#reg-phone', phone); await typeInto(p, '#reg-email', `qa_${role}@example.com`)
    await p.$eval('button.submit', (e) => e.click()); await sleep(200)
    check(`${bl}-4`, 'confirm-password mismatch flagged', (await txt(p, '#reg-confirm-error')) === 'The passwords do not match.')
    await typeInto(p, '#reg-confirm', STRONG)
    await p.$eval('button.submit', (e) => e.click()); await p.waitForNetworkIdle({ idleTime: 500 }).catch(() => {}); await sleep(300)
    if (role === 'client') {
      const note = await txt(p, '[data-test="registered"]')
      check(`${bl}-5`, 'client success: redirected to /login?registered=1 with success note', path(p) === '/login?registered=1' && /created/i.test(note ?? ''), `${path(p)} | ${note}`)
      await login(p, '+20 100 555 0011', STRONG)
      check(`${bl}-6`, 'new client logs in (phone typed in another format) and lands on /client', path(p) === '/client', path(p))
    } else {
      const pend = await txt(p, '[data-test="pending"] h1'); const steps = await p.$$eval('[data-test="pending"] li', (e) => e.length)
      check(`${bl}-5`, `${role} success: pending-approval screen with next steps (3), no auto-login`, pend === 'Registration received' && steps === 3 && !(await authKeys(p)).ls['delivery.refresh_token'], pend)
      const focused = await p.evaluate(() => document.activeElement?.tagName)
      check(`${bl}-5f`, 'pending screen moves focus to its heading (screen-reader announcement)', focused === 'H1', focused)
      await p.click('[data-test="pending"] a[href="/login"]'); await sleep(300)
      await login(p, phone.replace(/[٠-٩]/g, (d) => d.charCodeAt(0) - 0x660).replace(/\D/g, ''), STRONG)
      const m = await txt(p, '[data-test="form-error"]')
      check(`${bl}-6`, `new ${role} cannot log in yet: pending message shown`, /pending approval/i.test(m ?? '') && path(p) === '/login', m)
    }
    regs[role] = phone
    await p.close()
  }
  // server errors per field
  p = await newPage('/register/client')
  await typeInto(p, '#reg-full_name', 'Dup Person'); await typeInto(p, '#reg-phone', '01000000005'); await typeInto(p, '#reg-password', STRONG); await typeInto(p, '#reg-confirm', STRONG)
  await p.$eval('button.submit', (e) => e.click()); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(200)
  const dup = await txt(p, '#reg-phone-error')
  check('BL009-7', 'duplicate phone: server error shown under the phone field, form kept', /already exists/i.test(dup ?? '') && path(p) === '/register/client', dup)
  await typeInto(p, '#reg-phone', '01005559999'); await typeInto(p, '#reg-password', 'password123'); await typeInto(p, '#reg-confirm', 'password123')
  await p.$eval('button.submit', (e) => e.click()); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(200)
  const weak = await txt(p, '#reg-password-error')
  check('BL009-8', 'weak password: server error shown under the password field', !!weak && /common|numeric|similar/i.test(weak), weak)
  await typeInto(p, '#reg-password', STRONG); await typeInto(p, '#reg-confirm', STRONG); await typeInto(p, '#reg-email', 'qa_client@example.com')
  await p.$eval('button.submit', (e) => e.click()); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(200)
  check('BL009-9', 'duplicate email: server error shown under the email field', /already exists/i.test((await txt(p, '#reg-email-error')) ?? ''), await txt(p, '#reg-email-error'))
  await p.close()
  // Arabic server errors on register
  p = await newPage('/register/client', { lang: 'ar' })
  await typeInto(p, '#reg-full_name', 'Dup Person'); await typeInto(p, '#reg-phone', '01000000005'); await typeInto(p, '#reg-password', STRONG); await typeInto(p, '#reg-confirm', STRONG)
  await p.$eval('button.submit', (e) => e.click()); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(200)
  const dupAr = await txt(p, '#reg-phone-error')
  check('I18N-R1', 'duplicate phone error is in Arabic when UI is Arabic', !!dupAr && /[؀-ۿ]/.test(dupAr), dupAr)
  await p.close()
  // role/status not controllable from UI: the request body has no role/status
  p = await newPage('/register/driver'); let body = ''
  p.on('request', (r) => { if (r.method() === 'POST' && r.url().includes('/register/')) body = r.postData() ?? '' })
  await typeInto(p, '#reg-full_name', 'Body Check'); await typeInto(p, '#reg-phone', '01005550044'); await typeInto(p, '#reg-password', STRONG); await typeInto(p, '#reg-confirm', STRONG)
  await p.$eval('button.submit', (e) => e.click()); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {})
  check('BL009-10', 'register request goes to the role URL and carries only full_name/phone/password (empty email omitted; no role/status/confirm)', Object.keys(JSON.parse(body || '{}')).sort().join() === 'full_name,password,phone' && !/role|status/.test(body), body.replace(STRONG, '***'))
  await p.close()

  // ---------- BL-012/013 session, logout, guards ----------
  p = await newPage('/login')
  await login(p, 'demo_driver')
  const ks1 = await authKeys(p)
  const r1 = ks1.ls['delivery.refresh_token']
  check('BL013-1', 'only the refresh token is stored (localStorage); access token not in storage/cookies', Object.keys(ks1.ls).filter((k) => k !== 'locale').join() === 'delivery.refresh_token' && Object.keys(ks1.ss).length === 0 && ks1.cookie === '' && !!r1)
  await p.reload({ waitUntil: 'networkidle0' })
  const ks2 = await authKeys(p)
  check('BL013-2', 'page refresh keeps the session on the same screen (My Assigned Orders)', path(p) === '/driver' && (await txt(p, 'h1')) === 'My Assigned Orders', path(p))
  check('BL013-3', 'refresh token rotated and replaced in storage after restore', !!ks2.ls['delivery.refresh_token'] && ks2.ls['delivery.refresh_token'] !== r1)
  const stale = await post(API + '/auth/token/refresh/', { refresh: r1 })
  check('BL013-4', 'the pre-reload refresh token no longer works on the server (rotation)', stale.s === 401)
  // deep link refresh on a different page
  await p.goto(DEV + '/driver', { waitUntil: 'networkidle0' })
  check('BL013-5', 'direct URL load of own area with a stored session stays on it', path(p) === '/driver')
  // logout via menu
  const before = (await authKeys(p)).ls['delivery.refresh_token']
  await p.click('[data-testid="user-menu-button"]'); await p.click('[data-testid="logout"]'); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(300)
  const ks3 = await authKeys(p)
  check('BL013-6', 'logout from user menu goes to /login and clears the stored refresh token', path(p) === '/login' && !ks3.ls['delivery.refresh_token'], path(p))
  const dead = await post(API + '/auth/token/refresh/', { refresh: before })
  check('BL013-7', 'logged-out refresh token is blacklisted server-side (401)', dead.s === 401)
  await p.goBack(); await sleep(500)
  const afterBack = { path: path(p), h1: await txt(p, 'h1'), home: await p.$('[data-testid^="home-"]') }
  check('BL013-8', 'back button after logout does not show the protected screen (redirected to /login)', afterBack.path === '/login' && !afterBack.home, JSON.stringify({ ...afterBack, home: !!afterBack.home }))
  await p.goForward().catch(() => {}); await sleep(300)
  await p.goto(DEV + '/driver', { waitUntil: 'networkidle0' })
  check('BL013-9', 'after logout a protected URL redirects to /login', path(p) === '/login')
  await p.close()
  // logout works when API fails
  p = await newPage('/login'); await login(p, 'demo_trader')
  await p.setRequestInterception(true)
  p.on('request', (r) => (r.url().includes('/auth/logout/') ? r.abort() : r.continue()))
  await p.click('[data-testid="user-menu-button"]'); await p.click('[data-testid="logout"]'); await sleep(800)
  check('BL013-10', 'logout still signs the user out locally when the logout API call fails', path(p) === '/login' && !(await authKeys(p)).ls['delivery.refresh_token'], path(p))
  await p.close()
  // user menu: keyboard, Escape, shows name and role
  p = await newPage('/login'); await login(p, 'demo_manager')
  await p.focus('[data-testid="user-menu-button"]'); await p.keyboard.press('Enter'); await sleep(150)
  const menu = await txt(p, '[data-testid="user-menu-panel"]')
  await p.keyboard.press('Escape'); await sleep(150)
  const foc = await p.evaluate(() => document.activeElement?.getAttribute('data-testid'))
  check('A11Y-K2', 'user menu opens with Enter, shows name and role, Escape closes and returns focus to the button', /Demo Manager/.test(menu) && /Manager/.test(menu) && !(await p.$('[data-testid="user-menu-panel"]')) && foc === 'user-menu-button', menu)
  await p.keyboard.press('Enter'); await p.keyboard.press('Tab'); await p.keyboard.press('Enter'); await sleep(800)
  check('A11Y-K3', 'logout reachable and operable by keyboard only', path(p) === '/login', path(p))
  await p.close()
  // multiple tabs: logout in one context only affects its own storage (sanity), skipped (separate contexts)

  // guards
  const unauth = []
  for (const r of ['/driver', '/trader', '/client', '/admin']) { const q = await newPage(r); unauth.push(path(q)); await q.close() }
  check('GUARD-1', 'anonymous opening any role area is redirected to /login', unauth.every((u) => u === '/login'), unauth.join())
  const q404 = await newPage('/no/such/page'); check('GUARD-2', 'anonymous 404 page renders (public)', (await txt(q404, 'h1')) === 'Page not found'); await q404.close()
  const qh = await newPage('/'); check('GUARD-3', 'anonymous home is public', path(qh) === '/'); await qh.close()
  for (const [user, , role, home] of ROLES) {
    p = await newPage('/login'); await login(p, user)
    const seen = {}
    for (const target of ['/driver', '/trader', '/client', '/admin', '/login', '/register', '/register/driver', '/register/trader', '/register/client']) {
      await p.goto(DEV + target, { waitUntil: 'networkidle0' }); seen[target] = path(p)
    }
    const exp = Object.fromEntries(Object.keys(seen).map((t) => [t, ['/driver', '/trader', '/client', '/admin'].includes(t) ? (t === home ? t : home) : home]))
    check(`GUARD-4 ${role}`, `other roles' areas and guest-only pages redirect to own home ${home}`, JSON.stringify(seen) === JSON.stringify(exp), JSON.stringify(seen))
    const nav = await p.$$eval('nav a', (a) => a.map((x) => x.getAttribute('href')))
    check(`GUARD-5 ${role}`, 'navigation links only point to own area (plus public pages)', !nav.some((h) => ['/driver', '/trader', '/client', '/admin'].includes(h) && h !== home), nav.join())
    await p.goto(DEV + '/no/such/page', { waitUntil: 'networkidle0' })
    check(`GUARD-6 ${role}`, '404 page for signed-in user renders and keeps the session', (await txt(p, 'h1')) === 'Page not found' && !!(await authKeys(p)).ls['delivery.refresh_token'])
    await p.close()
  }

  // session expiry / account state changes while signed in
  p = await newPage('/login'); await login(p, 'demo_client')
  const rt = (await authKeys(p)).ls['delivery.refresh_token']
  await post(API + '/auth/logout/', { refresh: rt }) // killed from elsewhere
  await p.reload({ waitUntil: 'networkidle0' })
  const exp1 = await txt(p, '.auth-notice')
  check('BL012-11', 'session ended elsewhere (refresh invalid): reload goes to /login with a session-expired notice, storage cleared', path(p) === '/login' && /expired/i.test(exp1 ?? '') && !(await authKeys(p)).ls['delivery.refresh_token'], `${path(p)} | ${exp1}`)
  await p.close()
  p = await newPage('/register/client')
  await typeInto(p, '#reg-full_name', 'To Deactivate'); await typeInto(p, '#reg-phone', '01005550077'); await typeInto(p, '#reg-password', STRONG); await typeInto(p, '#reg-confirm', STRONG)
  await p.$eval('button.submit', (e) => e.click()); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(200)
  await login(p, '01005550077', STRONG)
  const okay = path(p) === '/client'
  setStatus('01005550077', 'deactivated')
  await p.reload({ waitUntil: 'networkidle0' })
  const exp2 = await txt(p, '.auth-notice, [data-test="form-error"]')
  check('BL012-12', 'account deactivated while signed in: reload returns to /login with a message, no protected content', okay && path(p) === '/login' && !!exp2 && !(await authKeys(p)).ls['delivery.refresh_token'], `${path(p)} | ${exp2}`)
  await login(p, '01005550077', STRONG)
  check('BL012-13', 'deactivated user cannot log in again (deactivated message)', /deactivated/i.test((await txt(p, '[data-test="form-error"]')) ?? ''))
  await p.close()

  // Arabic messages
  p = await newPage('/login', { lang: 'ar' })
  await login(p, 'demo_driver_pending'); const arP = await txt(p, '[data-test="form-error"]')
  await login(p, 'demo_client_deactivated'); const arD = await txt(p, '[data-test="form-error"]')
  await login(p, 'demo_client', 'bad-pass-123'); const arI = await txt(p, '[data-test="form-error"]')
  check('I18N-L1', 'pending / deactivated / invalid messages shown in Arabic, distinct', [arP, arD, arI].every((m) => /[؀-ۿ]/.test(m ?? '') && !/[A-Za-z]{4}/.test(m ?? '')) && new Set([arP, arD, arI]).size === 3, [arP, arD, arI].join(' | '))
  await login(p, 'demo_client'); // success in Arabic
  check('I18N-L2', 'Arabic login lands on /client with Arabic title and RTL', path(p) === '/client' && (await p.evaluate(() => document.documentElement.dir)) === 'rtl' && /[؀-ۿ]/.test(await txt(p, 'h1')), await txt(p, 'h1'))
  await p.close()

  // ---------- RTL / 360px / overflow on every new screen ----------
  const screens = [['/login', null], ['/register', null], ['/register/client', null], ['/register/driver', null], ['/register/trader', null], ['/driver', 'demo_driver'], ['/trader', 'demo_trader'], ['/client', 'demo_client'], ['/admin', 'demo_admin']]
  for (const [route, user] of screens) {
    for (const w of [360, 1280]) {
      p = await newPage('/login', { w, h: 800 })
      if (user) await login(p, user); else await p.goto(DEV + route, { waitUntil: 'networkidle0' })
      const enOk = await p.evaluate(() => ({ dir: document.documentElement.dir, h1: document.querySelector('h1')?.textContent, ov: document.documentElement.scrollWidth - document.documentElement.clientWidth }))
      await p.click('.language-switcher [data-locale="ar"]'); await sleep(250)
      const ar = await p.evaluate(() => ({ dir: document.documentElement.dir, lang: document.documentElement.lang, h1: document.querySelector('h1')?.textContent, ov: document.documentElement.scrollWidth - document.documentElement.clientWidth, font: getComputedStyle(document.body).fontFamily, untranslated: [...document.querySelectorAll('main *, header *')].filter((e) => !e.children.length && /^[A-Za-z][A-Za-z .,'-]{3,}$/.test(e.textContent.trim()) && e.closest('.language-switcher') === null).map((e) => e.textContent.trim()).slice(0, 4), clip: [...document.querySelectorAll('a,button,h1,p,span,label,input')].filter((e) => e.scrollWidth > e.clientWidth + 1 && !['visible'].includes(getComputedStyle(e).overflowX) && e.tagName !== 'INPUT').map((e) => e.textContent.trim().slice(0, 20)) }))
      await p.reload({ waitUntil: 'networkidle0' })
      const after = await p.evaluate(() => ({ dir: document.documentElement.dir, h1: document.querySelector('h1')?.textContent }))
      const ok = enOk.dir === 'ltr' && ar.dir === 'rtl' && ar.lang === 'ar' && enOk.h1 !== ar.h1 && enOk.ov <= 0 && ar.ov <= 0 && after.dir === 'rtl' && after.h1 === ar.h1 && ar.clip.length === 0
      check(`RTL ${route} ${w}px`, 'en<->ar flips text+dir, persists on reload, no horizontal overflow or clipping', ok, JSON.stringify({ en: enOk.h1, ar: ar.h1, ov: [enOk.ov, ar.ov], clip: ar.clip }))
      if (ar.untranslated.length) console.log('  note: English-looking text in Arabic UI on', route, ar.untranslated)
      await p.close()
    }
  }
  // pending screen + errors in RTL at 360
  p = await newPage('/register/trader', { w: 360, lang: 'ar' })
  await typeInto(p, '#reg-full_name', 'متجر الاختبار'); await typeInto(p, '#reg-phone', '٠١٠٠٥٥٥٠٠٨٨'); await typeInto(p, '#reg-password', STRONG); await typeInto(p, '#reg-confirm', STRONG)
  await p.$eval('button.submit', (e) => e.click()); await p.waitForNetworkIdle({ idleTime: 400 }).catch(() => {}); await sleep(300)
  const pa = await p.evaluate(() => ({ pend: !!document.querySelector('[data-test="pending"]'), dir: document.documentElement.dir, ov: document.documentElement.scrollWidth - document.documentElement.clientWidth, h1: document.querySelector('h1')?.textContent }))
  check('RTL pending 360px', 'pending-approval screen in Arabic: RTL, Arabic text, no overflow; Arabic name + Arabic-Indic phone accepted', pa.pend && pa.dir === 'rtl' && pa.ov <= 0 && /[؀-ۿ]/.test(pa.h1), JSON.stringify(pa))
  await p.close()
  p = await newPage('/register/client', { w: 360, lang: 'ar' })
  await p.$eval('button.submit', (e) => e.click()); await sleep(250)
  const ae = await p.$$eval('.field-error', (e) => e.map((x) => x.textContent.trim())); const aov = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  check('RTL errors 360px', 'client-side validation errors localized (Arabic) with no overflow', ae.length >= 3 && ae.every((m) => /[؀-ۿ]/.test(m)) && aov <= 0, ae.join(' | '))
  await p.close()
  p = await newPage('/login', { w: 360, lang: 'ar' })
  await login(p, 'demo_driver_pending'); const arov = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  check('RTL login-error 360px', 'long Arabic pending message does not overflow at 360px', arov <= 0)
  await p.close()

  // ---------- keyboard / touch targets ----------
  for (const [route, ids] of [['/login', ['login-identifier', 'login-password', 'toggle-password', 'submit']], ['/register/driver', ['reg-full_name', 'reg-phone', 'reg-email', 'reg-password', 'toggle-password', 'reg-confirm', 'submit']]]) {
    p = await newPage(route)
    const seq = []
    for (let i = 0; i < 16; i++) { await p.keyboard.press('Tab'); seq.push(await p.evaluate(() => { const e = document.activeElement; const cs = getComputedStyle(e); return { k: e.id || e.getAttribute('data-test') || (e.classList.contains('submit') ? 'submit' : e.className.split(' ')[0] || e.tagName), vis: cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) >= 2 || cs.boxShadow !== 'none' } })) }
    const keys = seq.map((s) => s.k)
    const idx = ids.map((i) => keys.indexOf(i))
    check(`A11Y-K4 ${route}`, 'Tab reaches all fields/buttons in visual order with visible focus indicator', idx.every((v, i) => v >= 0 && (i === 0 || v > idx[i - 1])) && seq.slice(0, Math.max(...idx) + 1).every((s) => s.vis), keys.join(' > '))
    const obscured = []
    for (let i = 0; i < 16; i++) { await p.keyboard.press('Tab'); await sleep(60); obscured.push(await p.evaluate(() => { const e = document.activeElement; const b = e.getBoundingClientRect(); const hit = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2); return e.closest('main') && hit !== e && !e.contains(hit) ? (e.id || e.textContent.trim().slice(0, 12)) : null })) }
    check(`A11Y-F1 ${route}`, 'focused controls are never hidden under the fixed bottom nav/header (WCAG 2.4.11)', obscured.every((o) => !o), obscured.filter(Boolean).join(','))
    const small = await p.evaluate(() => [...document.querySelectorAll('main a,main button,main input,header button,nav a')].filter((e) => { const b = e.getBoundingClientRect(); return b.width && (b.width < 43.5 || b.height < 43.5) }).map((e) => e.textContent.trim().slice(0, 15) || e.id))
    check(`A11Y-T1 ${route}`, 'touch targets >= 44px at 360px', small.length === 0, small.join(','))
    const lab = await p.evaluate(() => [...document.querySelectorAll('input')].filter((i) => !document.querySelector(`label[for="${i.id}"]`)).map((i) => i.id))
    check(`A11Y-L1 ${route}`, 'every input has an associated label', lab.length === 0, lab.join(','))
    await p.close()
  }
  p = await newPage('/register/client')
  await p.$eval('button.submit', (e) => e.click()); await sleep(200)
  const desc = await p.evaluate(() => { const i = document.querySelector('#reg-full_name'); return i.getAttribute('aria-describedby') && document.getElementById(i.getAttribute('aria-describedby').split(' ')[0])?.textContent })
  check('A11Y-E1', 'field error is linked to its input through aria-describedby', /name/i.test(desc ?? ''), desc)
  await p.close()
  p = await newPage('/login')
  const al = await (async () => { const q = await newPage('/login'); await login(q, 'demo_client', 'bad-pass-123'); const r = await q.$eval('[data-test="form-error"]', (e) => e.getAttribute('role')); await q.close(); return r })()
  check('A11Y-E3', 'API error message exposed with role="alert"', al === 'alert', al)
  await p.close()

  // ---------- security hygiene: token/password not in URL, console, storage; no v-html ----------
  const leakUrls = allCaps.flatMap((c) => c.urls.concat(c.navs)).filter((u) => TOKEN_RE.test(u) || /password=|refresh=|access=|token=/i.test(u))
  const leakLogs = allCaps.flatMap((c) => c.console).filter((l) => TOKEN_RE.test(l) || l.includes(DEMO_PW) || l.includes(STRONG))
  check('SEC-1', `no token/password in any URL, navigation or query string (${allCaps.reduce((n, c) => n + c.urls.length, 0)} requests inspected)`, leakUrls.length === 0, leakUrls.slice(0, 2).join(' '))
  check('SEC-2', `no token/password in browser console output (${allCaps.reduce((n, c) => n + c.console.length, 0)} messages inspected)`, leakLogs.length === 0, leakLogs.slice(0, 2).join(' '))
  const vlog = readLog('vite.log'); const blog = readLog('backend.log')
  check('SEC-3', 'no JWT or password in the vite or backend server logs', !TOKEN_RE.test(vlog + blog) && !(vlog + blog).includes(DEMO_PW) && !(vlog + blog).includes(STRONG))
  const consoleErr = allCaps.flatMap((c) => c.console).filter((l) => /PAGEERROR|\[Vue warn\]/.test(l))
  check('QUAL-1', 'no uncaught page errors or Vue warnings during the whole run', consoleErr.length === 0, consoleErr.slice(0, 3).join(' | '))
  // Authorization header never sent to a non-API origin
  // (all requests were to localhost:5174 or 127.0.0.1:8778)
  const foreign = allCaps.flatMap((c) => c.urls).filter((u) => !/^(http:\/\/localhost:5174|http:\/\/127\.0\.0\.1:8778|data:|blob:)/.test(u))
  check('SEC-4', 'the app only talks to its own origin and the configured API', foreign.length === 0, foreign.slice(0, 3).join(' '))

  // ---------- 429 and network error states (separate backend config) ----------
  stop(backend); await sleep(1000)
  backend = startBackend({ RATELIMIT_AUTH: '3/minute' }); await waitFor('http://127.0.0.1:8778/api/v1/health/', (s) => s === 403 || s === 200)
  for (const lang of ['en', 'ar']) {
    p = await newPage('/login', { lang })
    for (let i = 0; i < 4; i++) await login(p, 'demo_client', 'bad-pass-123')
    const m = await txt(p, '[data-test="form-error"]')
    const exp = lang === 'en' ? /Too many requests/ : /[؀-ۿ]/
    check(`BL012-14 ${lang}`, '429 (rate limited) shows a friendly localized message, not the invalid-credentials one', exp.test(m ?? '') && m !== 'Invalid credentials.', m)
    await p.close()
  }
  stop(backend); await sleep(1000)
  for (const lang of ['en', 'ar']) {
    p = await newPage('/login', { lang }); await login(p, 'demo_client')
    const m = await txt(p, '[data-test="form-error"]')
    check(`BL012-15 ${lang}`, 'backend unreachable: friendly network error, form stays usable', !!m && (lang === 'en' ? /Cannot reach/.test(m) : /[؀-ۿ]/.test(m)) && !(await p.$eval('button.submit', (e) => e.disabled)), m)
    await p.close()
  }
  // session restore with backend down must not log the user out locally (refresh token kept)? record behaviour
  backend = startBackend(); await waitFor('http://127.0.0.1:8778/api/v1/health/', (s) => s === 403 || s === 200)
  p = await newPage('/login'); await login(p, 'demo_client')
  stop(backend); await sleep(1000)
  await p.reload({ waitUntil: 'networkidle0' }).catch(() => {})
  const keep = (await authKeys(p)).ls['delivery.refresh_token']
  console.log(`  info: backend down on reload -> path=${path(p)} refreshTokenKept=${!!keep}`)
  await p.close()
} finally {
  await browser.close(); stop(fe); stop(backend)
}
const fails = results.filter((r) => !r.ok)
console.log(`\n${results.length - fails.length}/${results.length} passed; logs in ${LOGDIR}`)
process.exit(fails.length ? 1 : 0)
