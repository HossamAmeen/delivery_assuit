import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import AppShell from '@/components/AppShell.vue'
import LoginView from '@/views/LoginView.vue'
import { routes, installGuards } from '@/router'
import * as authApi from '@/api/auth'
import { useAuthStore, REFRESH_STORAGE_KEY } from '@/stores/auth'
import { i18n } from '@/i18n'
import { plugins, signIn } from './helpers'

vi.mock('@/api/health', () => ({ getHealth: vi.fn().mockResolvedValue({ status: 'healthy' }) }))
vi.mock('@/api/auth', async (orig) => ({ ...(await orig()), logout: vi.fn() }))
vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  listOrders: vi.fn().mockResolvedValue({ count: 0, next: null, previous: null, results: [] }),
  getDashboard: vi.fn().mockResolvedValue({
    period: 'all',
    drivers: { total: 0, active: 0, inactive: 0, pending: 0, rejected: 0 },
    traders: { total: 0, active: 0, inactive: 0, pending: 0, rejected: 0 },
    clients: { total: 0 },
    orders: { total: 0, pending: 0, in_progress: 0, delivered: 0, cancelled: 0 },
  }),
  getSummary: vi.fn().mockResolvedValue({
    total: 0,
    waiting_review: 0,
    waiting_for_driver: 0,
    in_progress: 0,
    delivered: 0,
    cancelled: 0,
  }),
}))

async function open(path, role) {
  const router = installGuards(createRouter({ history: createMemoryHistory(), routes }))
  const pinia = createPinia()
  setActivePinia(pinia)
  const auth = signIn(role)
  localStorage.setItem(REFRESH_STORAGE_KEY, 'old-refresh')
  router.push(path)
  await router.isReady()
  const wrapper = mount(AppShell, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return { wrapper, router, auth }
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})

describe('role home screens', () => {
  it.each([
    ['driver', '/driver', 'My Assigned Orders', 'Driver'],
    ['trader', '/trader', 'Dashboard', 'Trader'],
    ['client', '/client', 'Home', 'Client'],
    ['admin', '/admin', 'Dashboard', 'Admin'],
    ['manager', '/admin', 'Dashboard', 'Manager'],
  ])('%s sees the agreed title, name, role and empty state', async (role, path, title, label) => {
    const { wrapper } = await open(path, role)
    expect(wrapper.findAll('h1')).toHaveLength(1)
    expect(wrapper.find('h1').text()).toBe(title)
    expect(wrapper.find('[data-testid="home-name"]').text()).toBe('Test User')
    expect(wrapper.find('[data-testid="home-role"]').text()).toBe(label)
    // The client home has its own content instead of the placeholder (BL-044).
    expect(wrapper.find('[data-testid="home-empty"]').exists()).toBe(role !== 'client')
  })

  it('translates the title and role to Arabic', async () => {
    const { wrapper } = await open('/driver', 'driver')
    i18n.global.locale.value = 'ar'
    await flushPromises()
    expect(wrapper.find('h1').text()).toBe('طلباتي المسندة')
    expect(wrapper.find('[data-testid="home-role"]').text()).toBe('سائق')
  })

  it('each role lands on its own home from the guard', async () => {
    for (const [role, home] of [
      ['driver', '/driver'],
      ['trader', '/trader'],
      ['client', '/client'],
      ['admin', '/admin'],
      ['manager', '/admin'],
    ]) {
      const { router } = await open('/login', role)
      expect(router.currentRoute.value.path).toBe(home)
    }
  })
})

describe('user menu and logout', () => {
  it('is hidden for anonymous visitors', async () => {
    const { wrapper } = await open('/login', null)
    expect(wrapper.find('[data-testid="user-menu-button"]').exists()).toBe(false)
  })

  it('opens with name and role, toggles aria-expanded, closes on Escape and returns focus', async () => {
    const { wrapper } = await open('/driver', 'driver')
    const btn = wrapper.find('[data-testid="user-menu-button"]')
    expect(btn.attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('[data-testid="user-menu-panel"]').exists()).toBe(false)
    await btn.trigger('click')
    expect(btn.attributes('aria-expanded')).toBe('true')
    const panel = wrapper.find('[data-testid="user-menu-panel"]')
    expect(panel.text()).toContain('Test User')
    expect(panel.text()).toContain('Driver')
    await panel.trigger('keydown', { key: 'Escape' })
    await flushPromises()
    expect(wrapper.find('[data-testid="user-menu-panel"]').exists()).toBe(false)
  })

  it('logout blacklists the old token, clears the session and goes to login', async () => {
    authApi.logout.mockResolvedValue()
    const { wrapper, router, auth } = await open('/trader', 'trader')
    await wrapper.find('[data-testid="user-menu-button"]').trigger('click')
    await wrapper.find('[data-testid="logout"]').trigger('click')
    await flushPromises()
    expect(authApi.logout).toHaveBeenCalledWith()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.accessToken).toBeNull()
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
    expect(router.currentRoute.value.name).toBe('login')
    // Protected screens now redirect to login.
    await router.push('/trader')
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('login')
  })

  it('logout still works when the API call fails', async () => {
    authApi.logout.mockRejectedValue(new Error('offline'))
    const { wrapper, router, auth } = await open('/client', 'client')
    await wrapper.find('[data-testid="user-menu-button"]').trigger('click')
    await wrapper.find('[data-testid="logout"]').trigger('click')
    await flushPromises()
    expect(auth.isAuthenticated).toBe(false)
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
    expect(router.currentRoute.value.name).toBe('login')
  })
})

describe('session-expired notice', () => {
  it('shows a notice on login after an expired session', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().clearSession('expired')
    router.push('/login')
    await router.isReady()
    const w = mount(LoginView, { global: { plugins: plugins([router], pinia) } })
    expect(w.text()).toContain('Your session has expired')
  })
})
