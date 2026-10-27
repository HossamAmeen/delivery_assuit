import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { readFileSync } from 'node:fs'
import AppShell from '@/components/AppShell.vue'
import { routes } from '@/router'
import { createPinia, setActivePinia } from 'pinia'
import { plugins, signIn } from './helpers'
import { i18n } from '@/i18n'

vi.mock('@/api/health', () => ({ getHealth: vi.fn().mockResolvedValue({ status: 'healthy' }) }))

async function open(path, role = null) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  router.push(path)
  await router.isReady()
  const wrapper = mount(AppShell, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return wrapper
}

describe('AppShell', () => {
  it('has header, main and labelled navigation landmarks, plus a skip link', async () => {
    const w = await open('/')
    expect(w.find('header').exists()).toBe(true)
    expect(w.findAll('main')).toHaveLength(1)
    expect(w.find('main#main').exists()).toBe(true)
    expect(w.find('nav.bottom-nav').attributes('aria-label')).toBe('Main navigation')
    expect(w.find('a.skip-link').attributes('href')).toBe('#main')
  })

  it('shows the language switcher and bottom navigation on every screen', async () => {
    for (const path of ['/', '/driver', '/nope']) {
      const w = await open(path)
      expect(w.find('.language-switcher').exists()).toBe(true)
      expect(w.findAll('.bottom-nav a').map((a) => a.attributes('href'))).toEqual([
        '/login',
        '/register',
      ])
    }
  })

  it.each([
    ['driver', '/driver'],
    ['trader', '/trader'],
    ['client', '/client'],
    ['admin', '/admin'],
    ['manager', '/admin'],
  ])(
    'shows only the own area in the bottom nav and logout in the header menu for %s',
    async (role, home) => {
      const w = await open(home, role)
      expect(w.findAll('.bottom-nav a').map((a) => a.attributes('href'))).toEqual([home])
      expect(w.findAll('.bottom-nav button')).toHaveLength(0)
      await w.find('[data-testid="user-menu-button"]').trigger('click')
      expect(w.find('[data-testid="logout"]').text()).toBe('Sign out')
    },
  )

  it('marks the active area in the bottom navigation', async () => {
    const w = await open('/trader', 'trader')
    const active = w.findAll('.bottom-nav a.is-active')
    expect(active).toHaveLength(1)
    expect(active[0].attributes('href')).toBe('/trader')
  })

  it('translates the navigation when the language changes', async () => {
    const w = await open('/')
    i18n.global.locale.value = 'ar'
    await flushPromises()
    expect(w.find('nav.bottom-nav').attributes('aria-label')).toBe('التنقل الرئيسي')
    expect(w.find('a.skip-link').text()).toBe('التخطي إلى المحتوى')
  })
})

describe('shell styles', () => {
  const css = readFileSync('src/assets/main.css', 'utf8')
  const index = readFileSync('index.html', 'utf8')

  it('allows safe-area insets and sets a 44px touch target', () => {
    expect(index).toContain('viewport-fit=cover')
    expect(css).toContain('env(safe-area-inset-bottom)')
    expect(css).toContain('--touch-target: 2.75rem')
  })

  it('has visible focus styles', () => {
    expect(css).toContain(':focus-visible')
  })

  it('does not hard-code physical left/right', () => {
    expect(css).not.toMatch(/(margin|padding|border)-(left|right)\b/)
    expect(css).not.toMatch(/(^|[\s;{])(left|right)\s*:/)
    expect(css).not.toMatch(/text-align:\s*(left|right)/)
  })

  it('keeps the Arabic font in the font stack', () => {
    expect(css).toContain("'Noto Sans Arabic'")
  })
})
