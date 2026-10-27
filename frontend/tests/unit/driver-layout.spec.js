import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import DriverLayout from '@/layouts/DriverLayout.vue'
import ProfileView from '@/views/ProfileView.vue'
import AppHeader from '@/components/AppHeader.vue'
import * as authApi from '@/api/auth'
import { plugins, signIn } from './helpers'

vi.mock('@/api/auth', async (orig) => ({ ...(await orig()), me: vi.fn() }))
vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  listOrders: vi.fn().mockResolvedValue({ count: 0, next: null, previous: null, results: [] }),
}))

const ME = {
  id: 1,
  full_name: 'Omar Driver',
  phone: '01001234567',
  username: null,
  email: '',
  role: 'driver',
  status: 'active',
  rejection_reason: '',
}

beforeEach(() => {
  vi.clearAllMocks()
  authApi.me.mockResolvedValue(ME)
})

describe('driver navigation and profile', () => {
  it('links home, my orders and profile', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    signIn('driver')
    router.push('/driver')
    await router.isReady()
    const w = mount(DriverLayout, { global: { plugins: plugins([router], pinia) } })
    await flushPromises()
    const hrefs = w
      .find('.section-nav')
      .findAll('a')
      .map((a) => a.attributes('href'))
    expect(hrefs).toEqual(['/driver', '/driver/orders', '/driver/performance', '/account/profile'])
  })

  it('the profile shows name, phone and account status, and offers no status input', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    signIn('driver')
    const w = mount(ProfileView, { global: { plugins: plugins([router], pinia) } })
    await flushPromises()
    expect(w.find('#pf-full_name').element.value).toBe('Omar Driver')
    expect(w.find('#pf-phone').element.value).toBe('01001234567')
    expect(w.find('[data-test="status"]').text()).toBe('Active')
    const names = w.findAll('input, select').map((i) => i.attributes('name'))
    expect(names).not.toContain('status')
    expect(names).not.toContain('role')
  })

  it('change password and logout stay reachable from the header menu', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    signIn('driver')
    const w = mount(AppHeader, { global: { plugins: plugins([router], pinia) } })
    await w.find('[data-testid="user-menu-button"]').trigger('click')
    expect(w.find('a[href="/account/password"]').exists()).toBe(true)
    expect(w.find('[data-testid="logout"]').exists()).toBe(true)
  })
})
