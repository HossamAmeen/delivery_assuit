import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { plugins, signIn } from './helpers'
import { i18n } from '@/i18n'
import App from '@/App.vue'
import { routes } from '@/router'
import { getHealth } from '@/api/health'

vi.mock('@/api/health', () => ({ getHealth: vi.fn().mockResolvedValue({ status: 'healthy' }) }))

async function open(path) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  // The area tests below are about layouts, not guards: sign in as the matching role.
  const area = path.split('/')[1]
  const role = { driver: 'driver', trader: 'trader', client: 'client', admin: 'admin' }[area]
  if (role) signIn(role)
  router.push(path)
  await router.isReady()
  const wrapper = mount(App, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return wrapper
}

describe('home view', () => {
  it('renders the title and login/register links for anonymous visitors', async () => {
    const wrapper = await open('/')
    expect(wrapper.find('h1').text()).toBe('Delivery')
    const hrefs = wrapper.findAll('nav[aria-label="Areas"] a').map((a) => a.attributes('href'))
    expect(hrefs).toEqual(['/login', '/register'])
  })
})

describe('areas', () => {
  it.each(['driver', 'trader', 'client', 'admin'])('/%s renders its own layout', async (area) => {
    const wrapper = await open(`/${area}`)
    expect(wrapper.find(`[data-testid="layout-${area}"]`).exists()).toBe(true)
    const others = ['driver', 'trader', 'client', 'admin'].filter((a) => a !== area)
    for (const other of others) {
      expect(wrapper.find(`[data-testid="layout-${other}"]`).exists()).toBe(false)
    }
  })

  it('renders a 404 view for unknown routes', async () => {
    const wrapper = await open('/nope/nothing')
    expect(wrapper.find('h1').text()).toBe('Page not found')
  })
})

describe('language switch on screens', () => {
  it.each(['/', '/driver', '/nope'])('%s changes text when switched to Arabic', async (path) => {
    const wrapper = await open(path)
    const before = wrapper.find('h1').text()
    i18n.global.locale.value = 'ar'
    await flushPromises()
    expect(wrapper.find('h1').text()).not.toBe(before)
  })
})

describe('health widget visibility', () => {
  it('is shown in development', async () => {
    vi.stubEnv('DEV', true)
    const wrapper = await open('/')
    expect(wrapper.find('[data-testid="health-status"]').exists()).toBe(true)
    vi.unstubAllEnvs()
  })

  it('is not rendered and makes no health call in production', async () => {
    vi.stubEnv('DEV', false)
    vi.mocked(getHealth).mockClear()
    const wrapper = await open('/')
    expect(wrapper.find('[data-testid="health-status"]').exists()).toBe(false)
    expect(getHealth).not.toHaveBeenCalled()
    vi.unstubAllEnvs()
  })
})
