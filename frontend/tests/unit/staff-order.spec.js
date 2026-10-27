import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import StaffOrderView from '@/views/StaffOrderView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  getOrder: vi.fn(),
  setFee: vi.fn(),
  cancelOrder: vi.fn(),
}))

const ORDER = {
  id: 12,
  reference: 'ORD-000012',
  status: 'available',
  client: { id: 4, full_name: 'Mona', phone: '01001234567' },
  shop: { id: 1, name: 'Alpha Grill', phone: '01005550000' },
  driver: null,
  pickup: { name: 'Main', address: '12 Nile St' },
  delivery: { name: 'Home', address: '5 Garden St' },
  description: 'No onions',
  items: [
    { name: 'Kofta', quantity: 2, price: 10 },
    { name: 'Salad', quantity: 1, price: null },
  ],
  items_total: 20,
  delivery_fee: null,
  cancel_reason: '',
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
}

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('admin')
  router.push('/admin/orders/12')
  await router.isReady()
  const w = mount(StaffOrderView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.getOrder.mockResolvedValue(structuredClone(ORDER))
})

describe('staff order details', () => {
  it('shows details, prices, the total and the timeline in order', async () => {
    const w = await open()
    expect(w.find('[data-test="reference"]').text()).toBe('ORD-000012')
    expect(w.find('[data-test="client-phone"]').text()).toBe('01001234567')
    expect(w.findAll('[data-test="line"]')).toHaveLength(2)
    expect(w.findAll('[data-test="line-price"]')).toHaveLength(1)
    expect(w.find('[data-test="items-total"]').text()).toContain('20')
    expect(w.find('[data-test="fee"]').text()).toBe('Not set')
    const steps = w.findAll('[data-test="step"]')
    expect(steps.map((s) => s.find('strong').text())).toEqual([
      'Waiting for review',
      'Waiting for a driver',
    ])
    expect(steps[1].text()).toContain('Admin')
  })

  it('points to the right next screen for the status', async () => {
    let w = await open()
    expect(w.find('[data-test="go-assign"]').attributes('href')).toBe('/admin/orders/assign')
    expect(w.find('[data-test="go-review"]').exists()).toBe(false)
    ordersApi.getOrder.mockResolvedValue({ ...structuredClone(ORDER), status: 'created' })
    w = await open()
    expect(w.find('[data-test="go-review"]').attributes('href')).toBe('/admin/orders/review')
  })

  it('sets the fee as a number and reloads the order', async () => {
    ordersApi.setFee.mockResolvedValue({})
    const w = await open()
    await w.find('[data-test="fee-input"]').setValue(' 25.5 ')
    await w.find('[data-test="save-fee"]').trigger('click')
    await flushPromises()
    expect(ordersApi.setFee).toHaveBeenCalledWith(12, 25.5)
    expect(ordersApi.getOrder).toHaveBeenCalledTimes(2)
    expect(w.find('[data-test="notice"]').exists()).toBe(true)
  })

  it.each(['', 'abc', '-1', '100001', '1.234'])('blocks a bad fee (%s)', async (bad) => {
    const w = await open()
    await w.find('[data-test="fee-input"]').setValue(bad)
    await w.find('[data-test="save-fee"]').trigger('click')
    expect(ordersApi.setFee).not.toHaveBeenCalled()
    expect(w.find('[data-test="fee-error"]').exists()).toBe(true)
  })

  it('cancel needs a reason, then sends it trimmed and reloads', async () => {
    ordersApi.cancelOrder.mockResolvedValue({})
    const w = await open()
    await w.find('[data-test="cancel"]').trigger('click')
    await w.find('[data-test="confirm-cancel"]').trigger('click')
    expect(ordersApi.cancelOrder).not.toHaveBeenCalled()
    expect(w.find('[data-test="reason-error"]').exists()).toBe(true)
    await w.find('[data-test="cancel-reason-input"]').setValue('  Client unreachable ')
    await w.find('[data-test="confirm-cancel"]').trigger('click')
    await flushPromises()
    expect(ordersApi.cancelOrder).toHaveBeenCalledWith(12, 'Client unreachable')
    expect(ordersApi.getOrder).toHaveBeenCalledTimes(2)
  })

  it('a finished order offers no fee or cancel controls and shows the reason', async () => {
    ordersApi.getOrder.mockResolvedValue({
      ...structuredClone(ORDER),
      status: 'cancelled',
      cancel_reason: 'Client unreachable',
    })
    const w = await open()
    expect(w.find('[data-test="fee-input"]').exists()).toBe(false)
    expect(w.find('[data-test="cancel"]').exists()).toBe(false)
    expect(w.find('[data-test="cancel-reason"]').text()).toBe('Client unreachable')
  })

  it('a refused action reloads and shows the message; a crash stays friendly', async () => {
    ordersApi.setFee.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    await w.find('[data-test="fee-input"]').setValue('10')
    await w.find('[data-test="save-fee"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toMatch(/went wrong/i)
    ordersApi.setFee.mockRejectedValueOnce(
      new ApiError({
        status: 400,
        errors: { status: ['The fee of a finished order cannot be changed.'] },
      }),
    )
    await w.find('[data-test="save-fee"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toContain('finished')
    expect(ordersApi.getOrder).toHaveBeenCalledTimes(2)
  })

  it('says so when the order does not exist, and offers retry on errors', async () => {
    ordersApi.getOrder.mockRejectedValueOnce(new ApiError({ status: 404 }))
    let w = await open()
    expect(w.find('[data-test="missing"]').exists()).toBe(true)
    ordersApi.getOrder.mockRejectedValueOnce(new ApiError({ status: 500 }))
    w = await open()
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="reference"]').exists()).toBe(true)
  })

  it('is a staff route, after review and assign so those names still win', () => {
    const admin = routes.find((r) => r.path === '/admin')
    expect(admin.children.find((c) => c.name === 'admin-order').component).toBe(StaffOrderView)
    const paths = admin.children.map((c) => c.path)
    expect(paths).toContain('orders/review')
    expect(paths).toContain('orders/assign')
  })
})
