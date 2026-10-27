import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import DriverRankingView from '@/views/DriverRankingView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({ ...(await orig()), listDriverPerformance: vi.fn() }))

const ROWS = [
  {
    id: 5,
    full_name: 'Ali Driver',
    status: 'active',
    delivered: 8,
    cancelled: 1,
    average_rating: 4.5,
    rating_count: 6,
  },
  {
    id: 6,
    full_name: 'Omar Driver',
    status: 'active',
    delivered: 2,
    cancelled: 0,
    average_rating: null,
    rating_count: 0,
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
  const w = mount(DriverRankingView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.listDriverPerformance.mockResolvedValue(page(structuredClone(ROWS)))
})

describe('driver ranking', () => {
  it('shows delivered, cancelled, average rating and rating count per driver', async () => {
    const w = await open()
    const rows = w.findAll('[data-test="row"]')
    expect(rows[0].find('[data-test="delivered"]').text()).toBe('8')
    expect(rows[0].find('[data-test="average"]').text()).toBe('4.5')
    expect(rows[0].find('[data-test="count"]').text()).toBe('6')
    expect(rows[1].find('[data-test="average"]').text()).toBe('—')
    expect(rows[0].find('[data-test="open"]').attributes('href')).toBe('/admin/drivers/5')
  })

  it('starts sorted by delivered and sends the sort choice', async () => {
    const w = await open()
    expect(ordersApi.listDriverPerformance.mock.calls[0][0]).toEqual({
      month: '',
      ordering: 'delivered',
      page: 1,
    })
    await w.find('[data-test="ordering"]').setValue('rating')
    await flushPromises()
    expect(ordersApi.listDriverPerformance.mock.calls.at(-1)[0]).toEqual({
      month: '',
      ordering: 'rating',
      page: 1,
    })
  })

  it('filters by month and goes back to page 1', async () => {
    ordersApi.listDriverPerformance.mockResolvedValue(page(structuredClone(ROWS), { next: 'x' }))
    const w = await open()
    await w.find('[data-test="next"]').trigger('click')
    await flushPromises()
    expect(ordersApi.listDriverPerformance.mock.calls.at(-1)[0].page).toBe(2)
    await w.find('[data-test="month"]').setValue('2026-10')
    await flushPromises()
    expect(ordersApi.listDriverPerformance.mock.calls.at(-1)[0]).toEqual({
      month: '2026-10',
      ordering: 'delivered',
      page: 1,
    })
  })

  it('shows empty and error with retry', async () => {
    ordersApi.listDriverPerformance.mockResolvedValueOnce(page([]))
    expect((await open()).find('[data-test="empty"]').exists()).toBe(true)
    ordersApi.listDriverPerformance.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('is a staff route that does not clash with a driver id', () => {
    const admin = routes.find((r) => r.path === '/admin')
    expect(admin.children.find((c) => c.name === 'driver-ranking').component).toBe(
      DriverRankingView,
    )
    const detail = admin.children.find((c) => c.path.startsWith('drivers/:id'))
    expect(detail.path).toContain('\\d+')
  })
})
