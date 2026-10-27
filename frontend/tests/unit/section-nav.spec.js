import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import AdminLayout from '@/layouts/AdminLayout.vue'
import TraderLayout from '@/layouts/TraderLayout.vue'
import ClientLayout from '@/layouts/ClientLayout.vue'
import DriverLayout from '@/layouts/DriverLayout.vue'
import SectionNav from '@/components/SectionNav.vue'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  listOrders: vi.fn().mockResolvedValue({ count: 0, next: null, previous: null, results: [] }),
  getSummary: vi.fn().mockResolvedValue({ total: 0 }),
  getDashboard: vi.fn().mockResolvedValue({
    period: 'all',
    drivers: { total: 0 },
    traders: { total: 0 },
    clients: { total: 0 },
    orders: { total: 0 },
  }),
}))

async function nav(layout, role, path) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  router.push(path)
  await router.isReady()
  const w = mount(layout, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w.find('.section-nav')
}

describe('one navigation component for every area (BL-068)', () => {
  it.each([
    [AdminLayout, 'admin', '/admin', 'Admin sections'],
    [TraderLayout, 'trader', '/trader', 'Trader sections'],
    [ClientLayout, 'client', '/client', 'Client sections'],
    [DriverLayout, 'driver', '/driver', 'Driver sections'],
  ])(
    '%# uses SectionNav with a labelled landmark and touch-size links',
    async (layout, role, path, label) => {
      const n = await nav(layout, role, path)
      expect(n.exists()).toBe(true)
      expect(n.element.tagName).toBe('NAV')
      expect(n.attributes('aria-label')).toBe(label)
      const links = n.findAll('a')
      expect(links.length).toBeGreaterThanOrEqual(4)
      for (const a of links) expect(a.classes()).toContain('touch-link')
      expect(links[0].attributes('href')).toBe(path)
    },
  )

  it('every role has its home first and the active page marked', async () => {
    const n = await nav(ClientLayout, 'client', '/client')
    expect(n.findAll('a')[0].classes()).toContain('is-active')
  })

  it('marks only the exact page for entries that are prefixes of others', () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    const w = mount(SectionNav, {
      props: {
        label: 'admin.nav.label',
        items: [{ to: '/admin', label: 'admin.nav.dashboard', exact: true }],
      },
      global: { plugins: plugins([router]) },
    })
    expect(w.find('a').attributes('href')).toBe('/admin')
  })

  it('the admin nav reaches every staff screen', async () => {
    const n = await nav(AdminLayout, 'admin', '/admin')
    const hrefs = n.findAll('a').map((a) => a.attributes('href'))
    for (const h of [
      '/admin/approvals',
      '/admin/orders',
      '/admin/orders/review',
      '/admin/orders/assign',
      '/admin/drivers',
      '/admin/traders',
      '/admin/clients',
      '/admin/users',
      '/admin/audit',
    ])
      expect(hrefs).toContain(h)
  })
})
