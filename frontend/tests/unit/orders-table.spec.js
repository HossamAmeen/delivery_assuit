import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import OrdersTableView from '@/views/OrdersTableView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({ ...(await orig()), listOrders: vi.fn() }))

const ROWS = [
  {
    id: 12,
    reference: 'ORD-000012',
    status: 'assigned',
    client: { id: 4, full_name: 'Mona' },
    shop: { id: 1, name: 'Alpha Grill' },
    driver: { id: 5, full_name: 'Ali Driver' },
    pickup: { name: 'Main', address: '12 Nile St' },
    delivery: { name: 'Home', address: '5 Garden St' },
    delivery_fee: 25,
    created_at: '2026-10-27T10:00:00Z',
  },
  {
    id: 11,
    reference: 'ORD-000011',
    status: 'created',
    client: { id: 6, full_name: 'Sara' },
    shop: null,
    driver: null,
    pickup: { name: 'Office', address: '1 Tahrir Sq' },
    delivery: { name: 'Mum', address: '9 Rose St' },
    delivery_fee: null,
    created_at: '2026-10-26T10:00:00Z',
  },
]
const page = (results, extra = {}) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
  ...extra,
})

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('admin')
  const w = mount(OrdersTableView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.listOrders.mockResolvedValue(page(structuredClone(ROWS)))
})
afterEach(() => vi.useRealTimers())

describe('orders table', () => {
  it('shows every column the backlog asks for', async () => {
    const w = await open()
    const heads = w.findAll('th').map((h) => h.text())
    expect(heads).toHaveLength(9)
    const r = w.findAll('[data-test="row"]')
    expect(r).toHaveLength(2)
    expect(r[0].find('[data-test="client"]').text()).toBe('Mona')
    expect(r[0].find('[data-test="shop"]').text()).toBe('Alpha Grill')
    expect(r[0].find('[data-test="driver"]').text()).toBe('Ali Driver')
    expect(r[0].find('[data-test="status"]').text()).toBe('Assigned')
    expect(r[0].find('[data-test="fee"]').text()).toBe('25')
    expect(r[1].find('[data-test="shop"]').text()).toBe('—')
    expect(r[1].find('[data-test="fee"]').text()).toBe('—')
  })

  it('opens the order details from the reference', async () => {
    const w = await open()
    expect(w.findAll('[data-test="open"]')[0].attributes('href')).toBe('/admin/orders/12')
  })

  it('loads page 1 with no filters, and sends filters after a short pause', async () => {
    const w = await open()
    expect(ordersApi.listOrders.mock.calls[0][0]).toEqual({
      page: 1,
      status: '',
      created_from: '',
      created_to: '',
      search: '',
    })
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    await w.find('[data-test="status-filter"]').setValue('assigned')
    await w.find('[data-test="from"]').setValue('2026-10-01')
    await w.find('[data-test="to"]').setValue('2026-10-31')
    await w.find('[data-test="search"]').setValue(' ord-12 ')
    vi.advanceTimersByTime(300)
    await flushPromises()
    expect(ordersApi.listOrders.mock.calls.at(-1)[0]).toEqual({
      page: 1,
      status: 'assigned',
      created_from: '2026-10-01',
      created_to: '2026-10-31',
      search: 'ord-12',
    })
  })

  it('pages with next and previous', async () => {
    ordersApi.listOrders.mockResolvedValue(page(structuredClone(ROWS), { next: 'x' }))
    const w = await open()
    await w.find('[data-test="next"]').trigger('click')
    await flushPromises()
    expect(ordersApi.listOrders.mock.calls.at(-1)[0].page).toBe(2)
  })

  it('shows empty and error with retry', async () => {
    ordersApi.listOrders.mockResolvedValueOnce(page([]))
    let w = await open()
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
    ordersApi.listOrders.mockRejectedValueOnce(new ApiError({ isNetworkError: true }))
    w = await open()
    expect(w.find('[data-test="load-error"]').text()).toContain('offline')
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('is an admin and manager route', () => {
    const admin = routes.find((r) => r.path === '/admin')
    expect(admin.children.find((c) => c.name === 'admin-orders').component).toBe(OrdersTableView)
  })
})
