import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import DriverHistoryView from '@/views/DriverHistoryView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { formatDateTime } from '@/utils/format'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({ ...(await orig()), listOrders: vi.fn() }))

const ROWS = [
  {
    id: 14,
    reference: 'ORD-000014',
    status: 'cancelled',
    cancelled_at: '2026-10-27T12:00:00Z',
    delivered_at: null,
  },
  {
    id: 13,
    reference: 'ORD-000013',
    status: 'delivered',
    delivered_at: '2026-10-26T09:30:00Z',
    cancelled_at: null,
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
  signIn('driver')
  const w = mount(DriverHistoryView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.listOrders.mockResolvedValue(page(structuredClone(ROWS)))
})

describe('driver history', () => {
  it('asks only for finished orders', async () => {
    await open()
    expect(ordersApi.listOrders).toHaveBeenCalledWith({ scope: 'history', page: 1 })
  })

  it('shows reference, status and the date that matters, in the order given', async () => {
    const w = await open()
    const rows = w.findAll('[data-test="row"]')
    expect(rows.map((r) => r.find('[data-test="reference"]').text())).toEqual([
      'ORD-000014',
      'ORD-000013',
    ])
    expect(rows[0].find('[data-test="status"]').text()).toBe('Cancelled')
    expect(rows[1].find('[data-test="status"]').text()).toBe('Delivered')
    expect(rows[0].find('[data-test="when"]').text()).toBe(
      formatDateTime(ROWS[0].cancelled_at, 'en'),
    )
    expect(rows[1].find('[data-test="when"]').text()).toBe(
      formatDateTime(ROWS[1].delivered_at, 'en'),
    )
  })

  it('opens the order details', async () => {
    const w = await open()
    expect(w.findAll('[data-test="open"]')[1].attributes('href')).toBe('/driver/orders/13')
  })

  it('pages with next and previous', async () => {
    ordersApi.listOrders.mockResolvedValue(page(structuredClone(ROWS), { next: 'x' }))
    const w = await open()
    expect(w.find('[data-test="prev"]').attributes('disabled')).toBeDefined()
    await w.find('[data-test="next"]').trigger('click')
    await flushPromises()
    expect(ordersApi.listOrders.mock.calls.at(-1)[0]).toEqual({ scope: 'history', page: 2 })
  })

  it('shows empty and error with retry', async () => {
    ordersApi.listOrders.mockResolvedValueOnce(page([]))
    let w = await open()
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
    ordersApi.listOrders.mockRejectedValueOnce(new ApiError({ status: 500 }))
    w = await open()
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('is a driver route', () => {
    const driver = routes.find((r) => r.path === '/driver')
    expect(driver.children.find((c) => c.name === 'driver-orders').component).toBe(
      DriverHistoryView,
    )
  })
})
