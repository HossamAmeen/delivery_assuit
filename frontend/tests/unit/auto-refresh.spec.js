import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import DriverHomeView from '@/views/DriverHomeView.vue'
import OrderReviewView from '@/views/OrderReviewView.vue'
import OrderAssignView from '@/views/OrderAssignView.vue'
import ClientOrderView from '@/views/ClientOrderView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  listOrders: vi.fn(),
  getOrder: vi.fn(),
  listDrivers: vi.fn(),
}))

const TIMERS = ['setInterval', 'clearInterval', 'setTimeout', 'clearTimeout']
function setVisibility(state) {
  Object.defineProperty(document, 'visibilityState', { value: state, configurable: true })
}
function setOnline(value) {
  Object.defineProperty(window.navigator, 'onLine', { value, configurable: true })
}
const host = (refresh, options) =>
  mount(
    defineComponent({
      setup() {
        useAutoRefresh(refresh, options)
        return () => h('div')
      },
    }),
  )

beforeEach(() => {
  vi.clearAllMocks()
  vi.useFakeTimers({ toFake: TIMERS })
  setVisibility('visible')
  setOnline(true)
})
afterEach(() => {
  vi.useRealTimers()
  setVisibility('visible')
  setOnline(true)
})

describe('useAutoRefresh', () => {
  it('calls refresh on every interval and stops after unmount', async () => {
    const refresh = vi.fn().mockResolvedValue()
    const w = host(refresh, { interval: 1000 })
    for (let i = 0; i < 3; i++) await vi.advanceTimersByTimeAsync(1000)
    expect(refresh).toHaveBeenCalledTimes(3)
    w.unmount()
    vi.advanceTimersByTime(5000)
    expect(refresh).toHaveBeenCalledTimes(3)
  })

  it('skips while the tab is hidden and refreshes when it returns', async () => {
    const refresh = vi.fn().mockResolvedValue()
    host(refresh, { interval: 1000 })
    setVisibility('hidden')
    vi.advanceTimersByTime(3000)
    await flushPromises()
    expect(refresh).not.toHaveBeenCalled()
    setVisibility('visible')
    document.dispatchEvent(new Event('visibilitychange'))
    await flushPromises()
    expect(refresh).toHaveBeenCalledTimes(1)
  })

  it('skips while the browser is offline', async () => {
    const refresh = vi.fn().mockResolvedValue()
    host(refresh, { interval: 1000 })
    setOnline(false)
    vi.advanceTimersByTime(2000)
    await flushPromises()
    expect(refresh).not.toHaveBeenCalled()
  })

  it('never runs two refreshes at once', async () => {
    let finish
    const refresh = vi.fn(() => new Promise((r) => (finish = r)))
    host(refresh, { interval: 1000 })
    vi.advanceTimersByTime(3000)
    expect(refresh).toHaveBeenCalledTimes(1)
    finish()
    await flushPromises()
    vi.advanceTimersByTime(1000)
    expect(refresh).toHaveBeenCalledTimes(2)
  })

  it('swallows errors and keeps going', async () => {
    const refresh = vi.fn().mockRejectedValue(new Error('down'))
    host(refresh, { interval: 1000 })
    for (let i = 0; i < 2; i++) await vi.advanceTimersByTimeAsync(1000)
    expect(refresh).toHaveBeenCalledTimes(2)
  })
})

async function mountView(view, role, path) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  if (path) {
    router.push(path)
    await router.isReady()
  }
  const w = mount(view, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
const page = (results) => ({ count: results.length, next: null, previous: null, results })
const ORDER = {
  id: 12,
  reference: 'ORD-000012',
  status: 'assigned',
  next_action: 'pick_up',
  pickup: { name: 'A', address: 'addr one' },
  delivery: { name: 'B', address: 'addr two' },
  description: '',
  assigned_at: null,
}

describe('screens refresh quietly', () => {
  it('the driver home picks up a new assignment without a spinner', async () => {
    ordersApi.listOrders.mockResolvedValue(page([]))
    const w = await mountView(DriverHomeView, 'driver')
    expect(w.find('[data-testid="home-empty"]').exists()).toBe(true)
    ordersApi.listOrders.mockResolvedValue(page([ORDER]))
    vi.advanceTimersByTime(30000)
    await flushPromises()
    expect(w.find('[data-test="order"]').exists()).toBe(true)
    expect(w.find('[data-test="loading"]').exists()).toBe(false)
  })

  it('a failed quiet refresh keeps the list and shows no error', async () => {
    ordersApi.listOrders.mockResolvedValue(page([ORDER]))
    const w = await mountView(DriverHomeView, 'driver')
    ordersApi.listOrders.mockRejectedValue(new ApiError({ status: 500 }))
    vi.advanceTimersByTime(30000)
    await flushPromises()
    expect(w.find('[data-test="order"]').exists()).toBe(true)
    expect(w.find('[data-test="load-error"]').exists()).toBe(false)
  })

  it('the review queue keeps what the admin was typing when new orders arrive', async () => {
    const row = (id) => ({
      id,
      reference: `ORD-00001${id}`,
      shop: null,
      client: { full_name: 'Mona', phone: '0100' },
      pickup: { name: 'A', address: 'addr one' },
      delivery: { name: 'B', address: 'addr two' },
      items: [],
      description: 'x',
    })
    ordersApi.listOrders.mockResolvedValue(page([row(1)]))
    const w = await mountView(OrderReviewView, 'admin')
    await w.find('[data-test="reject"]').trigger('click')
    await w.find('[data-test="reason"]').setValue('Half-typed reason')
    ordersApi.listOrders.mockResolvedValue(page([row(2), row(1)]))
    vi.advanceTimersByTime(30000)
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
    expect(w.find('[data-test="reason"]').element.value).toBe('Half-typed reason')
  })

  it('the assign screen keeps the chosen driver when it refreshes', async () => {
    const o = (id) => ({
      id,
      reference: `ORD-00001${id}`,
      shop: null,
      pickup: { name: 'A', address: 'addr one' },
      delivery: { name: 'B', address: 'addr two' },
      delivery_fee: null,
    })
    ordersApi.listOrders.mockResolvedValue(page([o(1)]))
    ordersApi.listDrivers.mockResolvedValue(
      page([{ id: 5, full_name: 'Ali', has_active_order: false, active_order_reference: null }]),
    )
    const w = await mountView(OrderAssignView, 'admin')
    await w.find('[data-test="driver"]').setValue('5')
    ordersApi.listOrders.mockResolvedValue(page([o(2), o(1)]))
    vi.advanceTimersByTime(30000)
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
    const selects = w.findAll('[data-test="driver"]')
    expect(selects.find((s) => s.element.id === 'driver-1').element.value).toBe('5')
  })

  it('a client order screen updates its status and keeps a half-written cancel reason', async () => {
    const base = {
      id: 12,
      reference: 'ORD-000012',
      status: 'available',
      shop: null,
      client: { full_name: 'M' },
      driver: null,
      pickup: { name: 'A', address: 'addr one' },
      delivery: { name: 'B', address: 'addr two' },
      description: '',
      items: [],
      items_total: null,
      delivery_fee: null,
      cancel_reason: '',
      rating: null,
      history: [],
    }
    ordersApi.getOrder.mockResolvedValue(base)
    const w = await mountView(ClientOrderView, 'client', '/client/orders/12')
    await w.find('[data-test="cancel"]').trigger('click')
    await w.find('[data-test="reason"]').setValue('I changed')
    ordersApi.getOrder.mockResolvedValue({
      ...base,
      status: 'assigned',
      driver: { id: 5, full_name: 'Ali Driver' },
    })
    vi.advanceTimersByTime(30000)
    await flushPromises()
    expect(w.find('[data-test="status"]').text()).toBe('Assigned')
    expect(w.find('[data-test="driver"]').text()).toBe('Ali Driver')
    expect(w.find('[data-test="cancel"]').exists()).toBe(false)
  })
})
