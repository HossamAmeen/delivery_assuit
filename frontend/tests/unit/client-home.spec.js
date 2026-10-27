import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import ClientHomeView from '@/views/ClientHomeView.vue'
import { i18n } from '@/i18n'
import en from '@/locales/en.json'
import ar from '@/locales/ar.json'
import { plugins, signIn } from './helpers'

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  const w = mount(ClientHomeView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => vi.clearAllMocks())

describe('client home', () => {
  it('links both entries to their screens', async () => {
    const w = await open()
    expect(w.find('[data-test="entry-shop"]').attributes('href')).toBe('/client/shops')
    expect(w.find('[data-test="entry-direct"]').attributes('href')).toBe('/client/direct')
    expect(w.text()).toContain('Order from a shop')
    expect(w.text()).toContain('Deliver from place to place')
  })

  it('gives quick access to Profile, and My orders is a link', async () => {
    const w = await open()
    expect(w.find('[data-test="link-profile"]').attributes('href')).toBe('/account/profile')
    expect(w.find('[data-test="link-orders"]').attributes('href')).toBe('/client/orders')
  })

  it('shows no invented orders', async () => {
    const w = await open()
    expect(w.find('[data-testid="home-empty"]').exists()).toBe(false)
    expect(w.text()).not.toMatch(/active order|#\d+/i)
  })

  it('translates to Arabic', async () => {
    const w = await open()
    i18n.global.locale.value = 'ar'
    await flushPromises()
    expect(w.text()).toContain(ar.clientHome.shop)
    expect(w.text()).toContain(ar.clientHome.direct)
  })

  it('is the client route home', () => {
    const client = routes.find((r) => r.path === '/client')
    expect(client.children[0].component).toBe(ClientHomeView)
  })

  it('has the same clientHome keys in en and ar', () => {
    expect(Object.keys(en.clientHome).sort()).toEqual(Object.keys(ar.clientHome).sort())
  })
})
