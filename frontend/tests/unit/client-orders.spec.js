import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import OrderListView from '@/views/OrderListView.vue'
import ClientOrderView from '@/views/ClientOrderView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  listOrders: vi.fn(),
  getOrder: vi.fn(),
  cancelOrder: vi.fn(),
}))

const ORDER = (over = {}) => ({
  id: 12,
  reference: 'ORD-000012',
  status: 'created',
  client: { id: 4, full_name: 'Mona' },
  shop: { id: 1, name: 'Alpha Grill' },
  driver: null,
  pickup: { name: 'Main', address: '12 Nile St' },
  delivery: { name: 'Home', address: '5 Garden St' },
  description: 'No onions',
  items: [{ name: 'Kofta', quantity: 2, price: null }],
  items_total: null,
  delivery_fee: null,
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
  ],
  ...over,
})
const page = (results) => ({ count: results.length, next: null, previous: null, results })

async function openList() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  const w = mount(OrderListView, {
    props: { base: 'client' },
    global: { plugins: plugins([router], pinia) },
  })
  await flushPromises()
  return w
}
async function openDetail() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  router.push('/client/orders/12')
  await router.isReady()
  const w = mount(ClientOrderView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.getOrder.mockResolvedValue(ORDER())
  ordersApi.listOrders.mockResolvedValue(
    page([
      ORDER({ status: 'in_delivery' }),
      ORDER({ id: 11, reference: 'ORD-000011', status: 'delivered' }),
    ]),
  )
})

describe('client orders list', () => {
  it('links to the client details, highlights active orders, offers every status', async () => {
    const w = await openList()
    const rows = w.findAll('[data-test="row"]')
    expect(rows[0].find('[data-test="open"]').attributes('href')).toBe('/client/orders/12')
    expect(rows[0].find('[data-test="active"]').exists()).toBe(true)
    expect(rows[1].find('[data-test="active"]').exists()).toBe(false)
    const options = w
      .find('[data-test="status-filter"]')
      .findAll('option')
      .map((o) => o.attributes('value'))
    expect(options).toContain('created')
    expect(w.find('h1').text()).toBe('My orders')
  })

  it('filters by status', async () => {
    const w = await openList()
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    await w.find('[data-test="status-filter"]').setValue('created')
    vi.advanceTimersByTime(300)
    vi.useRealTimers()
    await flushPromises()
    expect(ordersApi.listOrders.mock.calls.at(-1)[0]).toEqual({
      page: 1,
      status: 'created',
      search: '',
    })
  })
})

describe('client order details', () => {
  it('shows waiting for review while created, with edit and cancel', async () => {
    const w = await openDetail()
    expect(w.find('[data-test="waiting"]').text()).toMatch(/waiting for review/i)
    expect(w.find('[data-test="edit"]').attributes('href')).toBe('/client/orders/12/edit')
    expect(w.find('[data-test="cancel"]').exists()).toBe(true)
    expect(w.find('[data-test="driver"]').text()).toBe('Waiting for a driver')
  })

  it('shows waiting for a driver while available', async () => {
    ordersApi.getOrder.mockResolvedValue(ORDER({ status: 'available' }))
    const w = await openDetail()
    expect(w.find('[data-test="waiting"]').text()).toMatch(/waiting for a driver/i)
    expect(w.find('[data-test="cancel"]').exists()).toBe(true)
  })

  it.each(['assigned', 'picked_up', 'in_delivery', 'delivered', 'cancelled'])(
    'offers no edit or cancel once %s',
    async (status) => {
      ordersApi.getOrder.mockResolvedValue(
        ORDER({
          status,
          driver: status === 'cancelled' ? null : { id: 5, full_name: 'Ali Driver' },
        }),
      )
      const w = await openDetail()
      expect(w.find('[data-test="edit"]').exists()).toBe(false)
      expect(w.find('[data-test="cancel"]').exists()).toBe(false)
      expect(w.find('[data-test="waiting"]').exists()).toBe(false)
    },
  )

  it('shows the driver name after assignment, never a phone', async () => {
    ordersApi.getOrder.mockResolvedValue(
      ORDER({ status: 'assigned', driver: { id: 5, full_name: 'Ali Driver' } }),
    )
    const w = await openDetail()
    expect(w.find('[data-test="driver"]').text()).toBe('Ali Driver')
    expect(w.html()).not.toMatch(/tel:/)
  })

  it('shows fee, prices and the timeline', async () => {
    ordersApi.getOrder.mockResolvedValue(
      ORDER({
        delivery_fee: 15,
        items: [{ name: 'Kofta', quantity: 2, price: 10 }],
        items_total: 20,
      }),
    )
    const w = await openDetail()
    expect(w.find('[data-test="fee"]').text()).toBe('15')
    expect(w.find('[data-test="items-total"]').text()).toContain('20')
    expect(w.findAll('[data-test="step"]')).toHaveLength(1)
  })

  it('cancel asks first, sends the optional reason, and reloads', async () => {
    ordersApi.cancelOrder.mockResolvedValue({})
    const w = await openDetail()
    await w.find('[data-test="cancel"]').trigger('click')
    expect(ordersApi.cancelOrder).not.toHaveBeenCalled()
    await w.find('[data-test="reason"]').setValue('  Changed my mind ')
    await w.find('[data-test="confirm-cancel"]').trigger('click')
    await flushPromises()
    expect(ordersApi.cancelOrder).toHaveBeenCalledWith(12, 'Changed my mind')
    expect(ordersApi.getOrder).toHaveBeenCalledTimes(2)
    expect(w.find('[data-test="notice"]').exists()).toBe(true)
  })

  it('cancel works without a reason and keep closes the box', async () => {
    ordersApi.cancelOrder.mockResolvedValue({})
    const w = await openDetail()
    await w.find('[data-test="cancel"]').trigger('click')
    await w.find('[data-test="keep"]').trigger('click')
    expect(w.find('[data-test="reason"]').exists()).toBe(false)
    await w.find('[data-test="cancel"]').trigger('click')
    await w.find('[data-test="confirm-cancel"]').trigger('click')
    await flushPromises()
    expect(ordersApi.cancelOrder).toHaveBeenCalledWith(12, '')
  })

  it('if a driver was assigned meanwhile, shows the message and the real state', async () => {
    ordersApi.cancelOrder.mockRejectedValue(
      new ApiError({ status: 403, message: 'You cannot make this status change.' }),
    )
    const w = await openDetail()
    ordersApi.getOrder.mockResolvedValue(
      ORDER({ status: 'assigned', driver: { id: 5, full_name: 'Ali Driver' } }),
    )
    await w.find('[data-test="cancel"]').trigger('click')
    await w.find('[data-test="confirm-cancel"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toContain('cannot make this status change')
    expect(w.find('[data-test="cancel"]').exists()).toBe(false)
  })

  it('a crash while cancelling stays friendly; 404 and retry work', async () => {
    ordersApi.cancelOrder.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await openDetail()
    await w.find('[data-test="cancel"]').trigger('click')
    await w.find('[data-test="confirm-cancel"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toMatch(/went wrong/i)
    ordersApi.getOrder.mockRejectedValueOnce(new ApiError({ status: 404 }))
    expect((await openDetail()).find('[data-test="missing"]').exists()).toBe(true)
  })

  it('routes belong to the client area', () => {
    const client = routes.find((r) => r.path === '/client')
    expect(client.children.find((c) => c.name === 'client-orders').props).toEqual({
      base: 'client',
    })
    expect(client.children.find((c) => c.name === 'client-order').component).toBe(ClientOrderView)
    setActivePinia(createPinia())
    signIn('driver')
    expect(authGuard({ meta: client.meta })).not.toBe(true)
  })
})

describe('search by reference (BL-028)', () => {
  it('sends the trimmed reference after a short pause and starts at page 1', async () => {
    const w = await openList()
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    await w.find('[data-test="search"]').setValue('  ord-000012 ')
    vi.advanceTimersByTime(300)
    vi.useRealTimers()
    await flushPromises()
    expect(ordersApi.listOrders.mock.calls.at(-1)[0]).toEqual({
      page: 1,
      status: '',
      search: 'ord-000012',
    })
  })

  it('combines the search with a status filter', async () => {
    const w = await openList()
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    await w.find('[data-test="search"]').setValue('ORD-1')
    await w.find('[data-test="status-filter"]').setValue('delivered')
    vi.advanceTimersByTime(300)
    vi.useRealTimers()
    await flushPromises()
    expect(ordersApi.listOrders.mock.calls.at(-1)[0]).toEqual({
      page: 1,
      status: 'delivered',
      search: 'ORD-1',
    })
  })

  it('shows the empty state when nothing matches', async () => {
    const w = await openList()
    ordersApi.listOrders.mockResolvedValue(page([]))
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    await w.find('[data-test="search"]').setValue('NOPE')
    vi.advanceTimersByTime(300)
    vi.useRealTimers()
    await flushPromises()
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
  })
})
