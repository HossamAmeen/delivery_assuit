import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import OrderAssignView from '@/views/OrderAssignView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  listOrders: vi.fn(),
  listDrivers: vi.fn(),
  assignOrder: vi.fn(),
}))

const ORDERS = [
  {
    id: 12,
    reference: 'ORD-000012',
    shop: { id: 1, name: 'Alpha Grill' },
    pickup: { name: 'Main', address: '12 Nile St' },
    delivery: { name: 'Home', address: '5 Garden St' },
    delivery_fee: 25,
  },
  {
    id: 11,
    reference: 'ORD-000011',
    shop: null,
    pickup: { name: 'Office', address: '1 Tahrir Sq' },
    delivery: { name: 'Mum', address: '9 Rose St' },
    delivery_fee: null,
  },
]
const DRIVERS = [
  {
    id: 5,
    full_name: 'Ali Driver',
    phone: '0100',
    has_active_order: false,
    active_order_reference: null,
  },
  {
    id: 6,
    full_name: 'Omar Driver',
    phone: '0101',
    has_active_order: true,
    active_order_reference: 'ORD-000009',
  },
]
const page = (results) => ({ count: results.length, next: null, previous: null, results })

async function open(role = 'admin') {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  const w = mount(OrderAssignView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.listOrders.mockResolvedValue(page(structuredClone(ORDERS)))
  ordersApi.listDrivers.mockResolvedValue(page(structuredClone(DRIVERS)))
})

describe('assign orders', () => {
  it('asks for available orders and active drivers', async () => {
    await open()
    expect(ordersApi.listOrders).toHaveBeenCalledWith({ status: 'available', page_size: 100 })
    expect(ordersApi.listDrivers).toHaveBeenCalled()
  })

  it('lists orders with places and the fee only when set', async () => {
    const w = await open()
    const rows = w.findAll('[data-test="row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].find('[data-test="fee"]').exists()).toBe(true)
    expect(rows[1].find('[data-test="fee"]').exists()).toBe(false)
    expect(rows[1].text()).toContain('Direct delivery')
  })

  it('shows a busy driver as unavailable with the order that keeps them busy', async () => {
    const w = await open()
    const options = w.findAll('[data-test="driver"]')[0].findAll('option')
    const busy = options.find((o) => o.text().includes('Omar'))
    expect(busy.attributes('disabled')).toBeDefined()
    expect(busy.text()).toContain('ORD-000009')
    expect(options.find((o) => o.text().includes('Ali')).attributes('disabled')).toBeUndefined()
  })

  it('needs a driver before calling the API', async () => {
    const w = await open()
    await w.findAll('[data-test="assign"]')[0].trigger('click')
    expect(ordersApi.assignOrder).not.toHaveBeenCalled()
    expect(w.find('[data-test="driver-error"]').exists()).toBe(true)
  })

  it('assigns, removes the row, and reloads the drivers', async () => {
    ordersApi.assignOrder.mockResolvedValue({ driver: { id: 5, full_name: 'Ali Driver' } })
    const w = await open()
    await w.findAll('[data-test="driver"]')[0].setValue('5')
    await w.findAll('[data-test="assign"]')[0].trigger('click')
    await flushPromises()
    expect(ordersApi.assignOrder).toHaveBeenCalledWith(12, 5)
    expect(w.findAll('[data-test="row"]')).toHaveLength(1)
    expect(w.find('[data-test="done"]').text()).toContain('Ali Driver')
    expect(ordersApi.listDrivers).toHaveBeenCalledTimes(2)
  })

  it('shows the server driver error on the field (driver became busy) and refreshes drivers', async () => {
    ordersApi.assignOrder.mockRejectedValue(
      new ApiError({
        status: 400,
        errors: { driver: ['This driver already has an active order.'] },
      }),
    )
    const w = await open()
    await w.findAll('[data-test="driver"]')[0].setValue('5')
    await w.findAll('[data-test="assign"]')[0].trigger('click')
    await flushPromises()
    expect(w.find('[data-test="driver-error"]').text()).toContain('already has an active order')
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
    expect(ordersApi.listDrivers).toHaveBeenCalledTimes(2)
  })

  it('refreshes the queue when someone else already assigned the order', async () => {
    ordersApi.assignOrder.mockRejectedValue(
      new ApiError({
        status: 400,
        errors: { status: ['Only an available order can be assigned.'] },
      }),
    )
    ordersApi.listOrders
      .mockResolvedValueOnce(page(structuredClone(ORDERS)))
      .mockResolvedValueOnce(page([structuredClone(ORDERS[1])]))
    const w = await open()
    await w.findAll('[data-test="driver"]')[0].setValue('5')
    await w.findAll('[data-test="assign"]')[0].trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toContain('available')
    expect(w.findAll('[data-test="row"]')).toHaveLength(1)
  })

  it('a server crash shows a friendly message and keeps the rows', async () => {
    ordersApi.assignOrder.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await open()
    await w.findAll('[data-test="driver"]')[0].setValue('5')
    await w.findAll('[data-test="assign"]')[0].trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toMatch(/went wrong/i)
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('does not double-submit while the request runs', async () => {
    let resolve
    ordersApi.assignOrder.mockReturnValue(new Promise((r) => (resolve = r)))
    const w = await open()
    await w.findAll('[data-test="driver"]')[0].setValue('5')
    await w.findAll('[data-test="assign"]')[0].trigger('click')
    await w.findAll('[data-test="assign"]')[0].trigger('click')
    expect(ordersApi.assignOrder).toHaveBeenCalledTimes(1)
    resolve({ driver: { full_name: 'Ali Driver' } })
    await flushPromises()
  })

  it('shows empty, no-drivers and the error state', async () => {
    ordersApi.listOrders.mockResolvedValueOnce(page([]))
    let w = await open()
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
    ordersApi.listDrivers.mockResolvedValueOnce(page([]))
    w = await open()
    expect(w.find('[data-test="no-drivers"]').exists()).toBe(true)
    ordersApi.listOrders.mockRejectedValueOnce(new ApiError({ status: 500 }))
    w = await open()
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
  })

  it('is an admin and manager route only', () => {
    const admin = routes.find((r) => r.path === '/admin')
    expect(admin.children.find((c) => c.name === 'order-assign').component).toBe(OrderAssignView)
    setActivePinia(createPinia())
    signIn('driver')
    expect(authGuard({ meta: admin.meta })).not.toBe(true)
  })
})
