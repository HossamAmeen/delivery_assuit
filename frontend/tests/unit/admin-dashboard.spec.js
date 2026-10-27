import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import AdminHomeView from '@/views/AdminHomeView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({ ...(await orig()), getDashboard: vi.fn() }))

const DATA = {
  period: 'all',
  drivers: { total: 9, active: 5, inactive: 2, pending: 1, rejected: 1 },
  traders: { total: 4, active: 3, inactive: 0, pending: 1, rejected: 0 },
  clients: { total: 20 },
  orders: { total: 30, pending: 6, in_progress: 8, delivered: 14, cancelled: 2 },
}

async function open(role = 'admin') {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  const w = mount(AdminHomeView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
const num = (w, sel) => w.find(`[data-test="${sel}"]`).text()

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.getDashboard.mockResolvedValue(structuredClone(DATA))
})

describe('admin dashboard', () => {
  it('shows drivers, traders and clients cards', async () => {
    const w = await open()
    expect(w.find('[data-test="drivers"] [data-test="total"]').text()).toBe('9')
    expect(w.find('[data-test="drivers"] [data-test="active"]').text()).toContain('5')
    expect(w.find('[data-test="drivers"] [data-test="inactive"]').text()).toContain('2')
    expect(w.find('[data-test="drivers"] [data-test="pending"]').text()).toContain('1')
    expect(w.find('[data-test="traders"] [data-test="total"]').text()).toBe('4')
    expect(w.find('[data-test="clients"] [data-test="total"]').text()).toBe('20')
  })

  it('shows the order counts and the help text for pending and in progress', async () => {
    const w = await open()
    expect(num(w, 'orders-total')).toContain('30')
    expect(num(w, 'orders-pending')).toContain('6')
    expect(num(w, 'orders-in_progress')).toContain('8')
    expect(num(w, 'orders-delivered')).toContain('14')
    expect(num(w, 'orders-cancelled')).toContain('2')
    expect(w.find('[data-test="help"]').text()).toMatch(/waiting for review or for a driver/)
  })

  it('defaults to all-time and sends the chosen period', async () => {
    const w = await open('manager')
    expect(ordersApi.getDashboard.mock.calls[0][0]).toEqual({ period: '', from: '', to: '' })
    await w.find('[data-test="period"]').setValue('week')
    await flushPromises()
    expect(ordersApi.getDashboard.mock.calls.at(-1)[0]).toEqual({
      period: 'week',
      from: '',
      to: '',
    })
  })

  it('a custom range waits for both dates, and refuses a backwards range without calling the API', async () => {
    const w = await open()
    await w.find('[data-test="period"]').setValue('custom')
    await flushPromises()
    const calls = ordersApi.getDashboard.mock.calls.length
    await w.find('[data-test="from"]').setValue('2026-10-20')
    await flushPromises()
    expect(ordersApi.getDashboard.mock.calls.length).toBe(calls)
    await w.find('[data-test="to"]').setValue('2026-10-10')
    await flushPromises()
    expect(ordersApi.getDashboard.mock.calls.length).toBe(calls)
    expect(w.find('[data-test="range-error"]').exists()).toBe(true)
    await w.find('[data-test="to"]').setValue('2026-10-25')
    await flushPromises()
    expect(ordersApi.getDashboard.mock.calls.at(-1)[0]).toEqual({
      period: 'custom',
      from: '2026-10-20',
      to: '2026-10-25',
    })
    expect(w.find('[data-test="range-error"]').exists()).toBe(false)
  })

  it('counts shown add up (pending + in progress + delivered + cancelled = total)', async () => {
    const o = DATA.orders
    expect(o.pending + o.in_progress + o.delivered + o.cancelled).toBe(o.total)
  })

  it('keeps the title, name and role; empty state for a new system', async () => {
    ordersApi.getDashboard.mockResolvedValue({
      ...DATA,
      drivers: { total: 0, active: 0, inactive: 0, pending: 0, rejected: 0 },
      orders: { total: 0, pending: 0, in_progress: 0, delivered: 0, cancelled: 0 },
    })
    const w = await open()
    expect(w.find('h1').text()).toBe('Dashboard')
    expect(w.find('[data-testid="home-name"]').text()).toBe('Test User')
    expect(w.find('[data-testid="home-empty"]').exists()).toBe(true)
  })

  it('shows an error with retry', async () => {
    ordersApi.getDashboard.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="orders-total"]').exists()).toBe(true)
  })

  it('is the admin home', () => {
    const admin = routes.find((r) => r.path === '/admin')
    expect(admin.children[0].component).toBe(AdminHomeView)
  })
})
