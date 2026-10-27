import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import DriverOrderView from '@/views/DriverOrderView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  getOrder: vi.fn(),
  advanceOrder: vi.fn(),
}))

const ORDER = {
  id: 12,
  reference: 'ORD-000012',
  status: 'assigned',
  next_action: 'pick_up',
  client: { id: 4, full_name: 'Mona', phone: '01001234567' },
  shop: { id: 1, name: 'Alpha Grill', phone: '01005550000' },
  pickup: { name: 'Main', address: '12 Nile St' },
  delivery: { name: 'Home', address: '5 Garden St' },
  description: 'No onions',
  items: [{ name: 'Kofta', quantity: 2 }],
  assigned_at: '2026-10-27T10:00:00Z',
  delivered_at: null,
  cancel_reason: '',
}

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('driver')
  router.push('/driver/orders/12')
  await router.isReady()
  const w = mount(DriverOrderView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.getOrder.mockResolvedValue(structuredClone(ORDER))
})

describe('driver order details', () => {
  it('shows everything the job involves', async () => {
    const w = await open()
    expect(w.find('[data-test="reference"]').text()).toBe('ORD-000012')
    expect(w.find('[data-test="status"]').text()).toBe('Assigned')
    expect(w.find('[data-test="pickup"]').text()).toContain('12 Nile St')
    expect(w.find('[data-test="delivery"]').text()).toContain('5 Garden St')
    expect(w.find('[data-test="description"]').text()).toBe('No onions')
    expect(w.find('[data-test="line"]').text()).toContain('2 × Kofta')
    expect(w.find('[data-test="shop-name"]').text()).toBe('Alpha Grill')
  })

  it('shows contact phones as call links when the server sends them', async () => {
    const w = await open()
    expect(w.find('[data-test="client-phone"]').attributes('href')).toBe('tel:01001234567')
    expect(w.find('[data-test="shop-phone"]').attributes('href')).toBe('tel:01005550000')
  })

  it('shows no phone when the server did not send one (finished orders)', async () => {
    ordersApi.getOrder.mockResolvedValue({
      ...structuredClone(ORDER),
      status: 'delivered',
      next_action: null,
      client: { id: 4, full_name: 'Mona' },
      shop: { id: 1, name: 'Alpha Grill' },
      delivered_at: '2026-10-27T11:00:00Z',
    })
    const w = await open()
    expect(w.find('[data-test="client-phone"]').exists()).toBe(false)
    expect(w.find('[data-test="shop-phone"]').exists()).toBe(false)
    expect(w.find('[data-test="delivered-at"]').exists()).toBe(true)
  })

  it('shows only the one valid action, and none once delivered', async () => {
    const w = await open()
    expect(w.findAll('[data-test="advance"]')).toHaveLength(1)
    expect(w.find('[data-test="advance"]').text()).toBe('Mark as picked up')
    ordersApi.getOrder.mockResolvedValue({
      ...structuredClone(ORDER),
      status: 'delivered',
      next_action: null,
    })
    const done = await open()
    expect(done.find('[data-test="advance"]').exists()).toBe(false)
  })

  it('walks the three steps in order, one tap each', async () => {
    ordersApi.advanceOrder
      .mockResolvedValueOnce({
        ...structuredClone(ORDER),
        status: 'picked_up',
        next_action: 'start_delivery',
      })
      .mockResolvedValueOnce({
        ...structuredClone(ORDER),
        status: 'in_delivery',
        next_action: 'deliver',
      })
      .mockResolvedValueOnce({ ...structuredClone(ORDER), status: 'delivered', next_action: null })
    const w = await open()
    const labels = [w.find('[data-test="advance"]').text()]
    for (let i = 0; i < 2; i++) {
      await w.find('[data-test="advance"]').trigger('click')
      await flushPromises()
      labels.push(w.find('[data-test="advance"]').text())
    }
    await w.find('[data-test="advance"]').trigger('click')
    await flushPromises()
    expect(labels).toEqual(['Mark as picked up', 'Start delivery', 'Mark as delivered'])
    expect(ordersApi.advanceOrder).toHaveBeenCalledTimes(3)
    expect(w.find('[data-test="status"]').text()).toBe('Delivered')
    expect(w.find('[data-test="advance"]').exists()).toBe(false)
  })

  it('disables the action while saving', async () => {
    let resolve
    ordersApi.advanceOrder.mockReturnValue(new Promise((r) => (resolve = r)))
    const w = await open()
    await w.find('[data-test="advance"]').trigger('click')
    expect(w.find('[data-test="advance"]').attributes('disabled')).toBeDefined()
    resolve({ ...structuredClone(ORDER), status: 'picked_up', next_action: 'start_delivery' })
    await flushPromises()
  })

  it('reloads the order when the step is refused (cancelled meanwhile)', async () => {
    ordersApi.advanceOrder.mockRejectedValue(
      new ApiError({ status: 400, errors: { status: ['final'] } }),
    )
    const w = await open()
    ordersApi.getOrder.mockResolvedValue({
      ...structuredClone(ORDER),
      status: 'cancelled',
      next_action: null,
      cancel_reason: 'Stopped by admin',
      client: { id: 4, full_name: 'Mona' },
    })
    await w.find('[data-test="advance"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="status"]').text()).toBe('Cancelled')
    expect(w.find('[data-test="cancel-reason"]').text()).toBe('Stopped by admin')
    expect(w.find('[data-test="advance"]').exists()).toBe(false)
  })

  it('says the order is not available on a 404 (not assigned to this driver)', async () => {
    ordersApi.getOrder.mockRejectedValue(new ApiError({ status: 404 }))
    const w = await open()
    expect(w.find('[data-test="missing"]').exists()).toBe(true)
    expect(w.find('[data-test="load-error"]').exists()).toBe(false)
  })

  it('shows an error with retry', async () => {
    ordersApi.getOrder.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="reference"]').exists()).toBe(true)
  })

  it('is a driver-only route', () => {
    const driver = routes.find((r) => r.path === '/driver')
    expect(driver.children.find((c) => c.name === 'driver-order').component).toBe(DriverOrderView)
    setActivePinia(createPinia())
    signIn('client')
    expect(authGuard({ meta: driver.meta })).not.toBe(true)
  })
})
