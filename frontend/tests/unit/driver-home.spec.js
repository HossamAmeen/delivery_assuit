import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import DriverHomeView from '@/views/DriverHomeView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { formatDateTime } from '@/utils/format'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  listOrders: vi.fn(),
  advanceOrder: vi.fn(),
}))

const ORDER = {
  id: 12,
  reference: 'ORD-000012',
  status: 'assigned',
  next_action: 'pick_up',
  pickup: { name: 'Main', address: '12 Nile St' },
  delivery: { name: 'Home', address: '5 Garden St' },
  description: 'No onions',
  assigned_at: '2026-10-27T10:00:00Z',
}
const page = (results) => ({ count: results.length, next: null, previous: null, results })

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('driver')
  const w = mount(DriverHomeView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.listOrders.mockResolvedValue(page([structuredClone(ORDER)]))
})

describe('driver home', () => {
  it('asks only for active orders', async () => {
    await open()
    expect(ordersApi.listOrders).toHaveBeenCalledWith({ scope: 'active', page_size: 50 })
  })

  it('shows the active order prominently with status, places, time and the next action', async () => {
    const w = await open()
    const card = w.find('[data-test="order"]')
    expect(card.find('[data-test="reference"]').text()).toBe('ORD-000012')
    expect(card.find('[data-test="status"]').text()).toBe('Assigned')
    expect(card.text()).toContain('12 Nile St')
    expect(card.text()).toContain('5 Garden St')
    expect(card.find('[data-test="assigned-at"]').text()).toContain(
      formatDateTime(ORDER.assigned_at, 'en'),
    )
    expect(card.find('[data-test="advance"]').text()).toBe('Mark as picked up')
    expect(card.find('[data-test="open"]').attributes('href')).toBe('/driver/orders/12')
  })

  it('shows a friendly empty state when nothing is assigned', async () => {
    ordersApi.listOrders.mockResolvedValue(page([]))
    const w = await open()
    expect(w.find('[data-testid="home-empty"]').text()).toMatch(/no assigned orders/i)
  })

  it('keeps the title, name and role', async () => {
    const w = await open()
    expect(w.find('h1').text()).toBe('My Assigned Orders')
    expect(w.find('[data-testid="home-name"]').text()).toBe('Test User')
  })

  it('refresh loads again', async () => {
    const w = await open()
    await w.find('[data-test="refresh"]').trigger('click')
    await flushPromises()
    expect(ordersApi.listOrders).toHaveBeenCalledTimes(2)
  })

  it('shows an error with retry, and the offline message', async () => {
    ordersApi.listOrders.mockRejectedValueOnce(new ApiError({ isNetworkError: true }))
    const w = await open()
    expect(w.find('[data-test="load-error"]').text()).toContain('offline')
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="order"]').exists()).toBe(true)
  })

  it('tapping the action sends one request and shows the next step', async () => {
    ordersApi.advanceOrder.mockResolvedValue({
      ...ORDER,
      status: 'picked_up',
      next_action: 'start_delivery',
    })
    const w = await open()
    await w.find('[data-test="advance"]').trigger('click')
    await flushPromises()
    expect(ordersApi.advanceOrder).toHaveBeenCalledWith(12)
    expect(w.find('[data-test="status"]').text()).toBe('Picked up')
    expect(w.find('[data-test="advance"]').text()).toBe('Start delivery')
  })

  it('drops the order from home once it is delivered', async () => {
    ordersApi.advanceOrder.mockResolvedValue({ ...ORDER, status: 'delivered', next_action: null })
    const w = await open()
    await w.find('[data-test="advance"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="order"]').exists()).toBe(false)
    expect(w.find('[data-testid="home-empty"]').exists()).toBe(true)
  })

  it('disables the button while the step is being saved (no double tap)', async () => {
    let resolve
    ordersApi.advanceOrder.mockReturnValue(new Promise((r) => (resolve = r)))
    const w = await open()
    await w.find('[data-test="advance"]').trigger('click')
    expect(w.find('[data-test="advance"]').attributes('disabled')).toBeDefined()
    await w.find('[data-test="advance"]').trigger('click')
    expect(ordersApi.advanceOrder).toHaveBeenCalledTimes(1)
    resolve({ ...ORDER, status: 'picked_up', next_action: 'start_delivery' })
    await flushPromises()
  })

  it('shows a friendly error on failure and reloads when the order changed elsewhere', async () => {
    ordersApi.advanceOrder.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    await w.find('[data-test="advance"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="advance-error"]').text()).toMatch(/went wrong/i)
    ordersApi.advanceOrder.mockRejectedValueOnce(
      new ApiError({ status: 400, errors: { status: ['final'] } }),
    )
    ordersApi.listOrders.mockResolvedValueOnce(page([]))
    await w.find('[data-test="advance"]').trigger('click')
    await flushPromises()
    expect(ordersApi.listOrders).toHaveBeenCalledTimes(2)
  })

  it('is the driver route home', () => {
    const driver = routes.find((r) => r.path === '/driver')
    expect(driver.children[0].component).toBe(DriverHomeView)
  })
})

describe('formatDateTime', () => {
  it('formats a valid time and ignores empty or bad input', () => {
    expect(formatDateTime('2026-10-27T10:00:00Z', 'en')).toContain('2026')
    expect(formatDateTime('', 'en')).toBe('')
    expect(formatDateTime(null, 'en')).toBe('')
    expect(formatDateTime('nonsense', 'en')).toBe('')
  })
})
