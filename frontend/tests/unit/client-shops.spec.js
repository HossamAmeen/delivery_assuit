import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import ClientShopsView from '@/views/ClientShopsView.vue'
import ClientShopView from '@/views/ClientShopView.vue'
import { ApiError } from '@/api/http'
import * as shopsApi from '@/api/shops'
import { plugins, signIn } from './helpers'

vi.mock('@/api/shops', async (orig) => ({
  ...(await orig()),
  listShops: vi.fn(),
  getShop: vi.fn(),
}))

const ROWS = [
  { id: 1, name: 'Alpha Grill', description: 'Grills' },
  { id: 2, name: 'Zeta Bakery', description: '' },
]
const page = (results, extra = {}) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
  ...extra,
})
const DETAIL = {
  id: 1,
  name: 'Alpha Grill',
  description: 'Grills',
  items: [
    { id: 7, name: 'Kofta', description: 'Hot', price: null },
    { id: 8, name: 'Salad', description: '', price: 12.5 },
  ],
  pickup_locations: [{ id: 3, name: 'Main', address: '12 Nile St', is_default: true }],
}

async function openList() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  const w = mount(ClientShopsView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
async function openDetail() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  router.push('/client/shops/1')
  await router.isReady()
  const w = mount(ClientShopView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  shopsApi.listShops.mockResolvedValue(page(ROWS))
  shopsApi.getShop.mockResolvedValue(DETAIL)
})
afterEach(() => vi.useRealTimers())

describe('shops list', () => {
  it('shows name and description and links to the details', async () => {
    const w = await openList()
    const rows = w.findAll('[data-test="row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Grills')
    expect(rows[0].find('[data-test="open"]').attributes('href')).toBe('/client/shops/1')
  })

  it('shows a friendly empty message', async () => {
    shopsApi.listShops.mockResolvedValue(page([]))
    const w = await openList()
    expect(w.find('[data-test="empty"]').text()).toMatch(/no shops/i)
  })

  it('shows an error with retry', async () => {
    shopsApi.listShops.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await openList()
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('searches by name after a short pause and returns to page 1', async () => {
    const w = await openList()
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    await w.find('[data-test="search"]').setValue('  zeta ')
    vi.advanceTimersByTime(300)
    await flushPromises()
    expect(shopsApi.listShops.mock.calls.at(-1)[0]).toEqual({ page: 1, search: 'zeta' })
  })

  it('pages with next and previous', async () => {
    shopsApi.listShops.mockResolvedValue(page(ROWS, { next: 'x' }))
    const w = await openList()
    expect(w.find('[data-test="prev"]').attributes('disabled')).toBeDefined()
    await w.find('[data-test="next"]').trigger('click')
    await flushPromises()
    expect(shopsApi.listShops.mock.calls.at(-1)[0].page).toBe(2)
  })
})

describe('shop details', () => {
  it('shows the shop, its items, and a price only where set', async () => {
    const w = await openDetail()
    expect(w.find('h1').text()).toBe('Alpha Grill')
    const items = w.findAll('[data-test="item"]')
    expect(items).toHaveLength(2)
    expect(items[0].find('[data-test="price"]').exists()).toBe(false)
    expect(items[1].find('[data-test="price"]').text()).toBe('12.5')
  })

  it('links to the order screen', async () => {
    const w = await openDetail()
    expect(w.find('[data-test="order"]').attributes('href')).toBe('/client/shops/1/order')
  })

  it('has no order link when the shop has no items', async () => {
    shopsApi.getShop.mockResolvedValue({ ...DETAIL, items: [] })
    const w = await openDetail()
    expect(w.find('[data-test="no-items"]').exists()).toBe(true)
    expect(w.find('[data-test="order"]').exists()).toBe(false)
  })

  it('says the shop is unavailable on a 404, not a failure', async () => {
    shopsApi.getShop.mockRejectedValue(new ApiError({ status: 404 }))
    const w = await openDetail()
    expect(w.find('[data-test="unavailable"]').exists()).toBe(true)
    expect(w.find('[data-test="load-error"]').exists()).toBe(false)
  })

  it('shows offline with retry on a network failure', async () => {
    shopsApi.getShop.mockRejectedValueOnce(new ApiError({ isNetworkError: true }))
    const w = await openDetail()
    expect(w.find('[data-test="load-error"]').text()).toContain('offline')
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.find('h1').text()).toBe('Alpha Grill')
  })
})

describe('routes', () => {
  it('are client-only children', () => {
    const client = routes.find((r) => r.path === '/client')
    const names = client.children.map((c) => c.name)
    expect(names).toEqual(expect.arrayContaining(['client-shops', 'client-shop']))
    setActivePinia(createPinia())
    signIn('trader')
    expect(authGuard({ meta: client.meta })).not.toBe(true)
  })
})
