import puppeteer from 'puppeteer-core'
import { readFileSync } from 'node:fs'
const axe = readFileSync(new URL('./node_modules/axe-core/axe.min.js', import.meta.url), 'utf8')
const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] })
let total = 0
for (const lang of ['en', 'ar']) for (const route of ['/', '/driver', '/trader', '/client', '/admin', '/nope']) for (const w of [360, 1280]) {
  const ctx = await b.createBrowserContext(); const p = await ctx.newPage(); await p.setViewport({ width: w, height: 700 })
  await p.evaluateOnNewDocument((l) => localStorage.setItem('locale', l), lang)
  await p.goto('http://localhost:5176' + route, { waitUntil: 'networkidle0' })
  await p.evaluate(axe)
  const r = await p.evaluate(() => axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'] }))
  const extra = await p.evaluate(() => ({ font: document.fonts.check('16px "Noto Sans Arabic"'), clipped: [...document.querySelectorAll('a,button,h1,p,span')].filter((e) => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible').map((e) => e.textContent.trim().slice(0, 20)) }))
  for (const v of r.violations) { total++; console.log(lang, route, w, v.id, v.impact, v.nodes.length, v.nodes[0].html.slice(0, 90)) }
  if (extra.clipped.length) console.log('CLIPPED', lang, route, w, extra.clipped)
  if (lang === 'ar' && !extra.font) console.log('ARABIC FONT NOT LOADED', route)
  await ctx.close()
}
console.log('axe violations total:', total)
await b.close()
