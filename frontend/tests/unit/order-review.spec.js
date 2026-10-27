import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import OrderReviewView from '@/views/OrderReviewView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  listOrders: vi.fn(),
  approveOrder: vi.fn(),
  rejectOrder: vi.fn(),
}))

const ROWS = [
  {
    id: 12,
    reference: 'ORD-000012',
    status: 'created',
    client: { id: 4, full_name: 'Mona', phone: '01001234567' },
    shop: { id: 1, name: 'Alpha Grill' },
    pickup: { name: 'Main', address: '12 Nile St' },
    delivery: { name: 'Home', address: '5 Garden St' },
    items: [{ name: 'Kofta', quantity: 2 }],
    description: 'No onions',
  },
  {
    id: 11,
    reference: 'ORD-000011',
    status: 'created',
    client: { id: 5, full_name: 'Sara', phone: '01009998888' },
    shop: null,
    pickup: { name: 'Office', address: '1 Tahrir Sq' },
    delivery: { name: 'Mum', address: '9 Rose St' },
    items: [],
    description: 'Documents',
  },
]
const page = (results) => ({ count: results.length, next: null, previous: null, results })

async function open(role = 'admin') {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  const w = mount(OrderReviewView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.listOrders.mockResolvedValue(page(structuredClone(ROWS)))
})

describe('order review', () => {
  it('asks only for orders waiting for review', async () => {
    await open()
    expect(ordersApi.listOrders).toHaveBeenCalledWith({ status: 'created', page_size: 100 })
  })

  it('shows full details: reference, client with phone, places, items, details', async () => {
    const w = await open()
    const rows = w.findAll('[data-test="row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].find('[data-test="reference"]').text()).toBe('ORD-000012')
    expect(rows[0].text()).toContain('Mona')
    expect(rows[0].text()).toContain('01001234567')
    expect(rows[0].find('[data-test="pickup"]').text()).toContain('12 Nile St')
    expect(rows[0].find('[data-test="line"]').text()).toContain('2 × Kofta')
    expect(rows[0].find('[data-test="description"]').text()).toBe('No onions')
    expect(rows[1].text()).toContain('Direct delivery')
  })

  it('shows empty, and error with retry', async () => {
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

  it('approves without a fee and removes the row', async () => {
    ordersApi.approveOrder.mockResolvedValue({})
    const w = await open()
    await w.findAll('[data-test="approve"]')[0].trigger('click')
    await w.find('[data-test="confirm"]').trigger('click')
    await flushPromises()
    expect(ordersApi.approveOrder).toHaveBeenCalledWith(12, null)
    expect(w.findAll('[data-test="row"]')).toHaveLength(1)
    expect(w.find('[data-test="done"]').text()).toContain('ORD-000012')
  })

  it('approves with a fee as a number', async () => {
    ordersApi.approveOrder.mockResolvedValue({})
    const w = await open()
    await w.findAll('[data-test="approve"]')[0].trigger('click')
    await w.find('[data-test="fee"]').setValue(' 25.5 ')
    await w.find('[data-test="confirm"]').trigger('click')
    await flushPromises()
    expect(ordersApi.approveOrder).toHaveBeenCalledWith(12, 25.5)
  })

  it.each(['abc', '-5', '100001', '1.234'])(
    'blocks a bad fee (%s) without calling the API',
    async (bad) => {
      const w = await open()
      await w.findAll('[data-test="approve"]')[0].trigger('click')
      await w.find('[data-test="fee"]').setValue(bad)
      await w.find('[data-test="confirm"]').trigger('click')
      expect(ordersApi.approveOrder).not.toHaveBeenCalled()
      expect(w.find('[data-test="fee-error"]').exists()).toBe(true)
    },
  )

  it('rejecting needs a reason, then sends it trimmed', async () => {
    ordersApi.rejectOrder.mockResolvedValue({})
    const w = await open()
    await w.findAll('[data-test="reject"]')[1].trigger('click')
    await w.find('[data-test="confirm"]').trigger('click')
    expect(ordersApi.rejectOrder).not.toHaveBeenCalled()
    expect(w.find('[data-test="reason-error"]').exists()).toBe(true)
    await w.find('[data-test="reason"]').setValue('  Address unclear ')
    await w.find('[data-test="confirm"]').trigger('click')
    await flushPromises()
    expect(ordersApi.rejectOrder).toHaveBeenCalledWith(11, 'Address unclear')
    expect(w.findAll('[data-test="row"]')).toHaveLength(1)
  })

  it('cancel closes the panel and calls nothing', async () => {
    const w = await open()
    await w.findAll('[data-test="reject"]')[0].trigger('click')
    await w.find('[data-test="cancel"]').trigger('click')
    expect(w.find('[data-test="reason"]').exists()).toBe(false)
    expect(ordersApi.rejectOrder).not.toHaveBeenCalled()
  })

  it('shows a friendly error and keeps the row on a server crash', async () => {
    ordersApi.approveOrder.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await open()
    await w.findAll('[data-test="approve"]')[0].trigger('click')
    await w.find('[data-test="confirm"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toMatch(/went wrong/i)
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('refreshes the queue when the order was already reviewed (400)', async () => {
    ordersApi.approveOrder.mockRejectedValue(
      new ApiError({
        status: 400,
        message: 'This status change is not allowed.',
        errors: { status: ['x'] },
      }),
    )
    ordersApi.listOrders
      .mockResolvedValueOnce(page(structuredClone(ROWS)))
      .mockResolvedValueOnce(page([structuredClone(ROWS[1])]))
    const w = await open()
    await w.findAll('[data-test="approve"]')[0].trigger('click')
    await w.find('[data-test="confirm"]').trigger('click')
    await flushPromises()
    expect(ordersApi.listOrders).toHaveBeenCalledTimes(2)
    expect(w.findAll('[data-test="row"]')).toHaveLength(1)
  })

  it('shows a server field error on the fee', async () => {
    ordersApi.approveOrder.mockRejectedValue(
      new ApiError({ status: 400, errors: { delivery_fee: ['Server: bad fee.'] } }),
    )
    const w = await open()
    await w.findAll('[data-test="approve"]')[0].trigger('click')
    await w.find('[data-test="fee"]').setValue('10')
    await w.find('[data-test="confirm"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="fee-error"]').text()).toBe('Server: bad fee.')
    expect(w.find('[data-test="fee"]').element.value).toBe('10')
  })

  it('is an admin and manager route only', () => {
    const admin = routes.find((r) => r.path === '/admin')
    expect(admin.children.find((c) => c.name === 'order-review').component).toBe(OrderReviewView)
    setActivePinia(createPinia())
    signIn('manager')
    expect(authGuard({ meta: admin.meta })).toBe(true)
    signIn('client')
    expect(authGuard({ meta: admin.meta })).not.toBe(true)
  })
})
