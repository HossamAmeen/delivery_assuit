import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import DriverPerformanceView from '@/views/DriverPerformanceView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({ ...(await orig()), getMyPerformance: vi.fn() }))

const M_OCT = { month: '2026-10', delivered: 3, cancelled: 1, average_rating: 3.5, rating_count: 2 }
const M_SEP = { month: '2026-09', delivered: 1, cancelled: 0, average_rating: 5, rating_count: 1 }
const ALL = {
  month: null,
  delivered: 4,
  cancelled: 1,
  average_rating: 4.0,
  rating_count: 3,
  months: [M_OCT, M_SEP],
}

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('driver')
  const w = mount(DriverPerformanceView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.getMyPerformance.mockImplementation(async (month) =>
    month ? { ...(month === '2026-10' ? M_OCT : M_SEP), months: [] } : structuredClone(ALL),
  )
})

describe('driver performance', () => {
  it('shows all-time delivered, cancelled and the average rating with its count', async () => {
    const w = await open()
    expect(ordersApi.getMyPerformance).toHaveBeenCalledWith('')
    expect(w.find('[data-test="delivered"] .count').text()).toBe('4')
    expect(w.find('[data-test="cancelled"] .count').text()).toBe('1')
    expect(w.find('[data-test="rating"]').text()).toContain('4 / 5')
    expect(w.find('[data-test="rating"]').text()).toContain('3 ratings')
  })

  it('the month picker lists the active months and updates the figures', async () => {
    const w = await open()
    const values = w
      .find('[data-test="month"]')
      .findAll('option')
      .map((o) => o.attributes('value'))
    expect(values).toEqual(['', '2026-10', '2026-09'])
    await w.find('[data-test="month"]').setValue('2026-10')
    await flushPromises()
    expect(ordersApi.getMyPerformance).toHaveBeenLastCalledWith('2026-10')
    expect(w.find('[data-test="delivered"] .count').text()).toBe('3')
    expect(w.find('[data-test="rating"]').text()).toContain('3.5 / 5')
    // the picker keeps all months after choosing one
    expect(w.find('[data-test="month"]').findAll('option')).toHaveLength(3)
  })

  it('shows a friendly empty state for a new driver, with no picker', async () => {
    ordersApi.getMyPerformance.mockResolvedValue({
      month: null,
      delivered: 0,
      cancelled: 0,
      average_rating: null,
      rating_count: 0,
      months: [],
    })
    const w = await open()
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
    expect(w.find('[data-test="month"]').exists()).toBe(false)
    expect(w.find('[data-test="rating"]').text()).toContain('No ratings yet')
  })

  it('never shows individual ratings or comments', async () => {
    const w = await open()
    expect(w.html()).not.toMatch(/comment/i)
  })

  it('shows an error with retry', async () => {
    ordersApi.getMyPerformance.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="delivered"]').exists()).toBe(true)
  })

  it('is a driver route', () => {
    const driver = routes.find((r) => r.path === '/driver')
    expect(driver.children.find((c) => c.name === 'driver-performance').component).toBe(
      DriverPerformanceView,
    )
  })
})
