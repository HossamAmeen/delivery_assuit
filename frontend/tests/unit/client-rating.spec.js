import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import ClientOrderView from '@/views/ClientOrderView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  getOrder: vi.fn(),
  rateOrder: vi.fn(),
}))

const ORDER = (over = {}) => ({
  id: 12,
  reference: 'ORD-000012',
  status: 'delivered',
  shop: null,
  client: { id: 4, full_name: 'Mona' },
  driver: { id: 5, full_name: 'Ali Driver' },
  pickup: { name: 'Main', address: '12 Nile St' },
  delivery: { name: 'Home', address: '5 Garden St' },
  description: 'Box',
  items: [],
  items_total: null,
  delivery_fee: null,
  cancel_reason: '',
  rating: null,
  history: [],
  ...over,
})

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  router.push('/client/orders/12')
  await router.isReady()
  const w = mount(ClientOrderView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.getOrder.mockResolvedValue(ORDER())
})

describe('rating the driver', () => {
  it('is offered on a delivered, unrated order', async () => {
    const w = await open()
    expect(w.find('[data-test="rating-form"]').exists()).toBe(true)
    expect(w.findAll('input[type="radio"]')).toHaveLength(5)
  })

  it.each(['created', 'available', 'assigned', 'picked_up', 'in_delivery', 'cancelled'])(
    'is not offered while %s',
    async (status) => {
      ordersApi.getOrder.mockResolvedValue(ORDER({ status }))
      const w = await open()
      expect(w.find('[data-test="rating-form"]').exists()).toBe(false)
    },
  )

  it('needs a score before it calls the API', async () => {
    const w = await open()
    await w.find('[data-test="rating-form"]').trigger('submit')
    expect(ordersApi.rateOrder).not.toHaveBeenCalled()
    expect(w.find('[data-test="rating-error"]').exists()).toBe(true)
  })

  it('sends the score and the trimmed optional comment, then reloads', async () => {
    ordersApi.rateOrder.mockResolvedValue({})
    const w = await open()
    await w.find('[data-test="score-4"]').setValue(true)
    await w.find('#rating-comment').setValue('  Quick and polite ')
    await w.find('[data-test="rating-form"]').trigger('submit')
    await flushPromises()
    expect(ordersApi.rateOrder).toHaveBeenCalledWith(12, 4, 'Quick and polite')
    expect(ordersApi.getOrder).toHaveBeenCalledTimes(2)
    expect(w.find('[data-test="notice"]').exists()).toBe(true)
  })

  it('works without a comment', async () => {
    ordersApi.rateOrder.mockResolvedValue({})
    const w = await open()
    await w.find('[data-test="score-5"]').setValue(true)
    await w.find('[data-test="rating-form"]').trigger('submit')
    await flushPromises()
    expect(ordersApi.rateOrder).toHaveBeenCalledWith(12, 5, '')
  })

  it('shows the rating instead of the form once rated, so it cannot be rated twice', async () => {
    ordersApi.getOrder.mockResolvedValue(
      ORDER({ rating: { score: 4, comment: 'Nice', created_at: 'x' } }),
    )
    const w = await open()
    expect(w.find('[data-test="rating-form"]').exists()).toBe(false)
    expect(w.find('[data-test="rating-score"]').text()).toContain('4')
    expect(w.find('[data-test="rating-comment"]').text()).toBe('Nice')
  })

  it('if it was rated meanwhile, shows the message and the real state', async () => {
    ordersApi.rateOrder.mockRejectedValue(
      new ApiError({ status: 400, errors: { status: ['This order was already rated.'] } }),
    )
    const w = await open()
    ordersApi.getOrder.mockResolvedValue(
      ORDER({ rating: { score: 5, comment: '', created_at: 'x' } }),
    )
    await w.find('[data-test="score-5"]').setValue(true)
    await w.find('[data-test="rating-form"]').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toContain('already rated')
    expect(w.find('[data-test="rating-form"]').exists()).toBe(false)
  })

  it('a crash is friendly and keeps the form; no double send', async () => {
    let reject
    ordersApi.rateOrder.mockReturnValue(new Promise((_, r) => (reject = r)))
    const w = await open()
    await w.find('[data-test="score-3"]').setValue(true)
    await w.find('[data-test="rating-form"]').trigger('submit')
    await w.find('[data-test="rating-form"]').trigger('submit')
    expect(ordersApi.rateOrder).toHaveBeenCalledTimes(1)
    reject(new ApiError({ status: 500 }))
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toMatch(/went wrong/i)
    expect(w.find('[data-test="rating-form"]').exists()).toBe(true)
  })
})
