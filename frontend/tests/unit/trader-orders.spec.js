import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import OrderListView from '@/views/OrderListView.vue'
import TraderOrderView from '@/views/TraderOrderView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  listOrders: vi.fn(),
  getOrder: vi.fn(),
}))

const ORDER = (over = {}) => ({
  id: 12,
  reference: 'ORD-000012',
  status: 'available',
  client: { id: 4, full_name: 'Mona' },
  shop: { id: 1, name: 'Alpha Grill' },
  driver: null,
  pickup: { name: 'Main', address: '12 Nile St' },
  delivery: { name: 'Home', address: '5 Garden St' },
  description: 'No onions',
  items: [{ name: 'Kofta', quantity: 2, price: 10 }],
  items_total: 20,
  delivery_fee: 5,
  cancel_reason: '',
  created_at: '2026-10-27T10:00:00Z',
  history: [
    {
      from_status: '',
      to_status: 'created',
      actor_name: 'Mona',
      reason: '',
      created_at: '2026-10-27T10:00:00Z',
    },
    {
      from_status: 'created',
      to_status: 'available',
      actor_name: 'Admin',
      reason: '',
      created_at: '2026-10-27T11:00:00Z',
    },
  ],
  ...over,
})
const page = (results, extra = {}) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
  ...extra,
})

async function openList(base = 'trader') {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(base)
  const w = mount(OrderListView, { props: { base }, global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
async function openDetail() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('trader')
  router.push('/trader/orders/12')
  await router.isReady()
  const w = mount(TraderOrderView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.listOrders.mockResolvedValue(
    page([ORDER(), ORDER({ id: 11, reference: 'ORD-000011', status: 'delivered' })]),
  )
  ordersApi.getOrder.mockResolvedValue(ORDER())
})

describe('trader orders list', () => {
  it('shows reference, status, places and date, and links to the trader details', async () => {
    const w = await openList('trader')
    const rows = w.findAll('[data-test="row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].find('[data-test="open"]').attributes('href')).toBe('/trader/orders/12')
    expect(rows[0].text()).toContain('Main → Home')
    expect(rows[0].find('[data-test="status"]').text()).toBe('Waiting for a driver')
    expect(rows[0].find('[data-test="date"]').text()).not.toBe('')
  })

  it('does not offer the unreviewed status to a trader', async () => {
    const w = await openList('trader')
    const options = w
      .find('[data-test="status-filter"]')
      .findAll('option')
      .map((o) => o.attributes('value'))
    expect(options).not.toContain('created')
    expect(options).toContain('available')
  })

  it('filters by status from page 1', async () => {
    const w = await openList('trader')
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    await w.find('[data-test="status-filter"]').setValue('delivered')
    vi.advanceTimersByTime(300)
    vi.useRealTimers()
    await flushPromises()
    expect(ordersApi.listOrders.mock.calls.at(-1)[0]).toEqual({
      page: 1,
      status: 'delivered',
      search: '',
    })
  })

  it('shows empty, error with retry, and pages', async () => {
    ordersApi.listOrders.mockResolvedValueOnce(page([]))
    let w = await openList('trader')
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
    ordersApi.listOrders.mockRejectedValueOnce(new ApiError({ status: 500 }))
    w = await openList('trader')
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
    ordersApi.listOrders.mockResolvedValue(page([ORDER()], { next: 'x' }))
    w = await openList('trader')
    await w.find('[data-test="next"]').trigger('click')
    await flushPromises()
    expect(ordersApi.listOrders.mock.calls.at(-1)[0].page).toBe(2)
  })
})

describe('trader order details', () => {
  it('shows details, no driver yet, and the timeline', async () => {
    const w = await openDetail()
    expect(w.find('[data-test="reference"]').text()).toBe('ORD-000012')
    expect(w.find('[data-test="driver"]').text()).toBe('Waiting for a driver')
    expect(w.findAll('[data-test="step"]')).toHaveLength(2)
    expect(w.find('[data-test="items-total"]').text()).toContain('20')
  })

  it('shows only the driver name once assigned, never a phone', async () => {
    ordersApi.getOrder.mockResolvedValue(
      ORDER({ status: 'assigned', driver: { id: 5, full_name: 'Ali Driver' } }),
    )
    const w = await openDetail()
    expect(w.find('[data-test="driver"]').text()).toBe('Ali Driver')
    expect(w.html()).not.toMatch(/tel:/)
  })

  it('a cancelled order shows as cancelled with the reason', async () => {
    ordersApi.getOrder.mockResolvedValue(
      ORDER({ status: 'cancelled', cancel_reason: 'Stopped by admin' }),
    )
    const w = await openDetail()
    expect(w.find('[data-test="status"]').text()).toBe('Cancelled')
    expect(w.find('[data-test="driver"]').exists()).toBe(false)
    expect(w.find('[data-test="cancel-reason"]').text()).toBe('Stopped by admin')
  })

  it('has no create, edit or cancel controls, and refresh reloads', async () => {
    const w = await openDetail()
    expect(w.findAll('button').map((b) => b.attributes('data-test'))).toEqual(['refresh'])
    await w.find('[data-test="refresh"]').trigger('click')
    await flushPromises()
    expect(ordersApi.getOrder).toHaveBeenCalledTimes(2)
  })

  it('says not available on 404 and retries errors', async () => {
    ordersApi.getOrder.mockRejectedValueOnce(new ApiError({ status: 404 }))
    let w = await openDetail()
    expect(w.find('[data-test="missing"]').exists()).toBe(true)
    ordersApi.getOrder.mockRejectedValueOnce(new ApiError({ isNetworkError: true }))
    w = await openDetail()
    expect(w.find('[data-test="load-error"]').text()).toContain('offline')
  })

  it('routes are trader-only', () => {
    const trader = routes.find((r) => r.path === '/trader')
    expect(trader.children.find((c) => c.name === 'trader-orders').props).toEqual({
      base: 'trader',
    })
    expect(trader.children.find((c) => c.name === 'trader-order').component).toBe(TraderOrderView)
    setActivePinia(createPinia())
    signIn('client')
    expect(authGuard({ meta: trader.meta })).not.toBe(true)
  })
})
