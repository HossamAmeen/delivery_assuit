import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import TraderHomeView from '@/views/TraderHomeView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({ ...(await orig()), getSummary: vi.fn() }))

const SUMMARY = {
  total: 12,
  waiting_review: 0,
  waiting_for_driver: 2,
  in_progress: 3,
  delivered: 5,
  cancelled: 2,
}

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('trader')
  const w = mount(TraderHomeView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
const counts = (w) =>
  Object.fromEntries(
    w
      .findAll('[data-test^="card-"]')
      .map((c) => [c.attributes('data-test'), c.find('[data-test="count"]').text()]),
  )

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.getSummary.mockResolvedValue({ ...SUMMARY })
})

describe('trader dashboard', () => {
  it('shows total, waiting for driver, in progress, delivered and cancelled', async () => {
    const w = await open()
    expect(counts(w)).toEqual({
      'card-total': '12',
      'card-waiting_for_driver': '2',
      'card-in_progress': '3',
      'card-delivered': '5',
      'card-cancelled': '2',
    })
    expect(w.find('h1').text()).toBe('Dashboard')
    expect(w.find('[data-test="see-orders"]').attributes('href')).toBe('/trader/orders')
  })

  it('the cards add up to the total', async () => {
    const w = await open()
    const c = counts(w)
    const parts = [
      'card-waiting_for_driver',
      'card-in_progress',
      'card-delivered',
      'card-cancelled',
    ]
    expect(parts.reduce((n, k) => n + Number(c[k]), 0)).toBe(Number(c['card-total']))
  })

  it('shows a friendly empty message with zero orders', async () => {
    ordersApi.getSummary.mockResolvedValue({
      ...SUMMARY,
      total: 0,
      waiting_for_driver: 0,
      in_progress: 0,
      delivered: 0,
      cancelled: 0,
    })
    const w = await open()
    expect(w.find('[data-testid="home-empty"]').exists()).toBe(true)
    expect(counts(w)['card-total']).toBe('0')
  })

  it('shows an error with retry', async () => {
    ordersApi.getSummary.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(counts(w)['card-total']).toBe('12')
  })

  it('is the trader home', () => {
    const trader = routes.find((r) => r.path === '/trader')
    expect(trader.children[0].component).toBe(TraderHomeView)
  })
})
