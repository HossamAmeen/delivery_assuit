import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import ClientEditOrderView from '@/views/ClientEditOrderView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import * as shopsApi from '@/api/shops'
import * as addressesApi from '@/api/addresses'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({
  ...(await orig()),
  getOrder: vi.fn(),
  updateOrder: vi.fn(),
}))
vi.mock('@/api/shops', async (orig) => ({ ...(await orig()), getShop: vi.fn() }))
vi.mock('@/api/addresses', async (orig) => ({ ...(await orig()), listAddresses: vi.fn() }))

const SHOP_ORDER = (over = {}) => ({
  id: 12,
  reference: 'ORD-000012',
  status: 'created',
  shop: { id: 1, name: 'Alpha Grill' },
  pickup: { name: 'Main', address: '12 Nile St', latitude: null, longitude: null },
  delivery: { name: 'Home', address: '5 Garden St', latitude: 30.1, longitude: 31.2 },
  description: 'No onions',
  items: [{ name: 'Kofta', quantity: 2, price: null }],
  ...over,
})
const DIRECT = {
  id: 13,
  reference: 'ORD-000013',
  status: 'available',
  shop: null,
  pickup: { name: 'Office', address: '1 Tahrir Sq', latitude: null, longitude: null },
  delivery: { name: 'Mum', address: '9 Rose St', latitude: null, longitude: null },
  description: 'Documents',
  items: [],
}
const SHOP = {
  id: 1,
  name: 'Alpha Grill',
  items: [
    { id: 7, name: 'Kofta', price: null },
    { id: 8, name: 'Salad', price: null },
  ],
  pickup_locations: [
    { id: 3, name: 'Main', address: '12 Nile St', is_default: true },
    { id: 5, name: 'Second', address: '2 Side St', is_default: false },
  ],
}

async function open(orderId = 12) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  router.push(`/client/orders/${orderId}/edit`)
  await router.isReady()
  const w = mount(ClientEditOrderView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return { w, router }
}

beforeEach(() => {
  vi.clearAllMocks()
  ordersApi.getOrder.mockResolvedValue(SHOP_ORDER())
  shopsApi.getShop.mockResolvedValue(structuredClone(SHOP))
  addressesApi.listAddresses.mockResolvedValue({ results: [] })
})

describe('edit a shop order', () => {
  it('fills the form with the current values', async () => {
    const { w } = await open()
    expect(w.find('#edit-description').element.value).toBe('No onions')
    expect(w.find('#edit-del-name').element.value).toBe('Home')
    expect(w.find('#edit-del-latitude').element.value).toBe('30.1')
    expect(w.find('[data-test="rereview"]').exists()).toBe(false)
  })

  it('saves only what the form holds: places and note, no items unless asked', async () => {
    ordersApi.updateOrder.mockResolvedValue({})
    const { w, router } = await open()
    await w.find('#edit-del-address').setValue('6 Garden St')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(ordersApi.updateOrder).toHaveBeenCalledWith(12, {
      description: 'No onions',
      delivery: { name: 'Home', address: '6 Garden St', latitude: 30.1, longitude: 31.2 },
    })
    expect(router.currentRoute.value.fullPath).toBe('/client/orders/12')
  })

  it('changes items with quantities prefilled by name, and picks a pickup place', async () => {
    ordersApi.updateOrder.mockResolvedValue({})
    const { w } = await open()
    await w.find('[data-test="change-items"]').setValue(true)
    expect(w.find('[data-test="qty-7"]').element.value).toBe('2')
    expect(w.find('[data-test="qty-8"]').element.value).toBe('')
    await w.find('[data-test="qty-8"]').setValue('1')
    await w.find('[data-test="pickup"]').setValue('5')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    const body = ordersApi.updateOrder.mock.calls[0][1]
    expect(body.items).toEqual([
      { item: 7, quantity: 2 },
      { item: 8, quantity: 1 },
    ])
    expect(body.pickup_location).toBe(5)
  })

  it('blocks removing every item', async () => {
    const { w } = await open()
    await w.find('[data-test="change-items"]').setValue(true)
    await w.find('[data-test="qty-7"]').setValue('0')
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.updateOrder).not.toHaveBeenCalled()
    expect(w.find('[data-test="items-error"]').exists()).toBe(true)
  })

  it('a closed shop still lets the delivery place be edited', async () => {
    shopsApi.getShop.mockRejectedValue(new ApiError({ status: 404 }))
    ordersApi.updateOrder.mockResolvedValue({})
    const { w } = await open()
    expect(w.find('[data-test="shop-gone"]').exists()).toBe(true)
    expect(w.find('[data-test="change-items"]').exists()).toBe(false)
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(ordersApi.updateOrder).toHaveBeenCalledTimes(1)
  })

  it('shows server errors on the field and keeps the typed values', async () => {
    ordersApi.updateOrder.mockRejectedValue(
      new ApiError({ status: 400, errors: { delivery: { address: ['Server: bad address.'] } } }),
    )
    const { w } = await open()
    await w.find('#edit-del-address').setValue('6 Garden St')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('#edit-del-address-error').text()).toBe('Server: bad address.')
    expect(w.find('#edit-del-address').element.value).toBe('6 Garden St')
  })
})

describe('edit a direct delivery', () => {
  beforeEach(() => ordersApi.getOrder.mockResolvedValue(structuredClone(DIRECT)))

  it('shows the re-review notice for an approved order', async () => {
    const { w } = await open(13)
    expect(w.find('[data-test="rereview"]').exists()).toBe(true)
  })

  it('sends both places and the details', async () => {
    ordersApi.updateOrder.mockResolvedValue({})
    const { w } = await open(13)
    await w.find('#edit-pick-name').setValue('HQ')
    await w.find('#edit-description').setValue('  New details ')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    const body = ordersApi.updateOrder.mock.calls[0][1]
    expect(body.pickup.name).toBe('HQ')
    expect(body.delivery.name).toBe('Mum')
    expect(body.description).toBe('New details')
    expect(shopsApi.getShop).not.toHaveBeenCalled()
  })

  it('keeps the details mandatory', async () => {
    const { w } = await open(13)
    await w.find('#edit-description').setValue('ab')
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.updateOrder).not.toHaveBeenCalled()
    expect(w.find('[data-test="description-error"]').exists()).toBe(true)
  })

  it('does not double-submit', async () => {
    let resolve
    ordersApi.updateOrder.mockReturnValue(new Promise((r) => (resolve = r)))
    const { w } = await open(13)
    await w.find('[data-test="form"]').trigger('submit')
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.updateOrder).toHaveBeenCalledTimes(1)
    resolve({})
    await flushPromises()
  })
})

describe('when editing is not allowed', () => {
  it.each(['assigned', 'picked_up', 'in_delivery', 'delivered', 'cancelled'])(
    '%s shows no form',
    async (status) => {
      ordersApi.getOrder.mockResolvedValue(SHOP_ORDER({ status }))
      const { w } = await open()
      expect(w.find('[data-test="locked"]').exists()).toBe(true)
      expect(w.find('[data-test="form"]').exists()).toBe(false)
    },
  )

  it('a refusal at save time (driver assigned meanwhile) reloads and locks the form', async () => {
    const { w } = await open()
    ordersApi.updateOrder.mockRejectedValue(
      new ApiError({ status: 403, message: 'This order can no longer be edited.' }),
    )
    ordersApi.getOrder.mockResolvedValue(SHOP_ORDER({ status: 'assigned' }))
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="locked"]').exists()).toBe(true)
  })

  it('404 says not available; network failure offers retry', async () => {
    ordersApi.getOrder.mockRejectedValueOnce(new ApiError({ status: 404 }))
    expect((await open()).w.find('[data-test="missing"]').exists()).toBe(true)
    ordersApi.getOrder.mockRejectedValueOnce(new ApiError({ isNetworkError: true }))
    const { w } = await open()
    expect(w.find('[data-test="load-error"]').text()).toContain('offline')
  })

  it('route belongs to the client area', () => {
    const client = routes.find((r) => r.path === '/client')
    expect(client.children.find((c) => c.name === 'client-order-edit').component).toBe(
      ClientEditOrderView,
    )
  })
})
