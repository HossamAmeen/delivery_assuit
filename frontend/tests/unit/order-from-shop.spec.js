import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import OrderFromShopView from '@/views/OrderFromShopView.vue'
import { ApiError } from '@/api/http'
import * as shopsApi from '@/api/shops'
import * as ordersApi from '@/api/orders'
import * as addressesApi from '@/api/addresses'
import { choicePayload, choiceProblems, emptyChoice } from '@/utils/places'
import { plugins, signIn } from './helpers'

vi.mock('@/api/shops', async (orig) => ({ ...(await orig()), getShop: vi.fn() }))
vi.mock('@/api/orders', async (orig) => ({ ...(await orig()), createOrder: vi.fn() }))
vi.mock('@/api/addresses', async (orig) => ({ ...(await orig()), listAddresses: vi.fn() }))

const SHOP = {
  id: 1,
  name: 'Alpha Grill',
  description: '',
  items: [
    { id: 7, name: 'Kofta', description: '', price: null },
    { id: 8, name: 'Salad', description: '', price: 12.5 },
  ],
  pickup_locations: [{ id: 3, name: 'Main', address: '12 Nile St', is_default: true }],
}
const ADDRESSES = [{ id: 4, name: 'Home', address: '5 Garden St', latitude: null, longitude: null }]
const CREATED = { id: 12, reference: 'ORD-000012', status: 'created' }

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  router.push('/client/shops/1/order')
  await router.isReady()
  const w = mount(OrderFromShopView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
const typeDelivery = async (w, values) => {
  for (const [id, v] of Object.entries(values)) await w.find(`#ord-del-${id}`).setValue(v)
}

beforeEach(() => {
  vi.clearAllMocks()
  shopsApi.getShop.mockResolvedValue(structuredClone(SHOP))
  addressesApi.listAddresses.mockResolvedValue({ results: [] })
})

describe('order from a shop', () => {
  it('lists the items with quantity inputs and shows the fixed pickup', async () => {
    const w = await open()
    expect(w.findAll('[data-test="line"]')).toHaveLength(2)
    expect(w.find('[data-test="pickup-fixed"]').text()).toContain('12 Nile St')
    expect(w.find('[data-test="pickup"]').exists()).toBe(false)
  })

  it('blocks submit with no items and no delivery place, without calling the API', async () => {
    const w = await open()
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.createOrder).not.toHaveBeenCalled()
    expect(w.find('[data-test="items-error"]').exists()).toBe(true)
    expect(w.find('#ord-del-name-error').exists()).toBe(true)
    expect(w.find('#ord-del-address-error').exists()).toBe(true)
  })

  it('treats a quantity of 0 as not ordered', async () => {
    const w = await open()
    await w.find('[data-test="qty-7"]').setValue('0')
    await typeDelivery(w, { name: 'Home', address: '5 Garden St' })
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.createOrder).not.toHaveBeenCalled()
  })

  it('sends the chosen items, the default pickup and a typed delivery place', async () => {
    ordersApi.createOrder.mockResolvedValue(CREATED)
    const w = await open()
    await w.find('[data-test="qty-7"]').setValue('2')
    await w.find('[data-test="qty-8"]').setValue('1')
    await typeDelivery(w, {
      name: ' Home ',
      address: ' 5 Garden St ',
      latitude: '30.1',
      longitude: '31.2',
    })
    await w.find('#ord-description').setValue('  No onions ')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(ordersApi.createOrder).toHaveBeenCalledWith({
      shop: 1,
      items: [
        { item: 7, quantity: 2 },
        { item: 8, quantity: 1 },
      ],
      pickup_location: 3,
      delivery: { name: 'Home', address: '5 Garden St', latitude: 30.1, longitude: 31.2 },
      description: 'No onions',
    })
  })

  it('shows the reference after success', async () => {
    ordersApi.createOrder.mockResolvedValue(CREATED)
    const w = await open()
    await w.find('[data-test="qty-7"]').setValue('1')
    await typeDelivery(w, { name: 'Home', address: '5 Garden St' })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="reference"]').text()).toBe('ORD-000012')
    expect(w.find('[data-test="form"]').exists()).toBe(false)
  })

  it('offers a pickup choice when the shop has several', async () => {
    const shop = structuredClone(SHOP)
    shop.pickup_locations.push({ id: 5, name: 'Second', address: '2 Side St', is_default: false })
    shopsApi.getShop.mockResolvedValue(shop)
    ordersApi.createOrder.mockResolvedValue(CREATED)
    const w = await open()
    expect(w.find('[data-test="pickup"]').element.value).toBe('3')
    await w.find('[data-test="pickup"]').setValue('5')
    await w.find('[data-test="qty-7"]').setValue('1')
    await typeDelivery(w, { name: 'Home', address: '5 Garden St' })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(ordersApi.createOrder.mock.calls[0][0].pickup_location).toBe(5)
  })

  it('uses a saved address when the client has one', async () => {
    addressesApi.listAddresses.mockResolvedValue({ results: ADDRESSES })
    ordersApi.createOrder.mockResolvedValue(CREATED)
    const w = await open()
    expect(w.find('[data-test="ord-del-mode-saved"]').element.checked).toBe(true)
    await w.find('[data-test="qty-7"]').setValue('1')
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.createOrder).not.toHaveBeenCalled()
    await w.find('[data-test="ord-del-saved"]').setValue('4')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    const body = ordersApi.createOrder.mock.calls[0][0]
    expect(body.delivery_saved_address).toBe(4)
    expect(body.delivery).toBeUndefined()
  })

  it('can switch from a saved address to typing a place', async () => {
    addressesApi.listAddresses.mockResolvedValue({ results: ADDRESSES })
    const w = await open()
    await w.find('[data-test="ord-del-mode-typed"]').setValue(true)
    expect(w.find('#ord-del-name').exists()).toBe(true)
  })

  it('still lets the client type a place if saved addresses fail to load', async () => {
    addressesApi.listAddresses.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await open()
    expect(w.find('#ord-del-name').exists()).toBe(true)
  })

  it('shows server errors on the matching field and keeps the typed values', async () => {
    ordersApi.createOrder.mockRejectedValue(
      new ApiError({
        status: 400,
        errors: {
          items: ['One or more items are not available from this shop.'],
          delivery: { address: ['Server: bad address.'] },
        },
      }),
    )
    const w = await open()
    await w.find('[data-test="qty-7"]').setValue('3')
    await typeDelivery(w, { name: 'Home', address: '5 Garden St' })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="items-error"]').text()).toContain('not available')
    expect(w.find('#ord-del-address-error').text()).toBe('Server: bad address.')
    expect(w.find('[data-test="qty-7"]').element.value).toBe('3')
    expect(w.find('#ord-del-name').element.value).toBe('Home')
  })

  it('shows a closed shop as a page message', async () => {
    ordersApi.createOrder.mockRejectedValue(
      new ApiError({ status: 400, errors: { shop: ['This shop is not available for orders.'] } }),
    )
    const w = await open()
    await w.find('[data-test="qty-7"]').setValue('1')
    await typeDelivery(w, { name: 'Home', address: '5 Garden St' })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').text()).toContain('not available')
  })

  it('a network failure keeps the form and shows a friendly message', async () => {
    ordersApi.createOrder.mockRejectedValue(new ApiError({ isNetworkError: true }))
    const w = await open()
    await w.find('[data-test="qty-7"]').setValue('1')
    await typeDelivery(w, { name: 'Home', address: '5 Garden St' })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').exists()).toBe(true)
    expect(w.find('[data-test="form"]').exists()).toBe(true)
  })

  it('disables the button while the order is being placed (no double submit)', async () => {
    let resolve
    ordersApi.createOrder.mockReturnValue(new Promise((r) => (resolve = r)))
    const w = await open()
    await w.find('[data-test="qty-7"]').setValue('1')
    await typeDelivery(w, { name: 'Home', address: '5 Garden St' })
    await w.find('[data-test="form"]').trigger('submit')
    expect(w.find('[data-test="submit"]').attributes('disabled')).toBeDefined()
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.createOrder).toHaveBeenCalledTimes(1)
    resolve(CREATED)
    await flushPromises()
  })

  it('says so when the shop is no longer available', async () => {
    shopsApi.getShop.mockRejectedValue(new ApiError({ status: 404 }))
    const w = await open()
    expect(w.find('[data-test="unavailable"]').exists()).toBe(true)
    expect(w.find('[data-test="form"]').exists()).toBe(false)
  })
})

describe('place choice helpers', () => {
  it('start in saved mode only when there are saved addresses', () => {
    expect(emptyChoice(true).mode).toBe('saved')
    expect(emptyChoice(false).mode).toBe('typed')
  })
  it('validate and build the payload for each mode', () => {
    const saved = { ...emptyChoice(true), savedId: '4' }
    expect(choiceProblems(saved)).toEqual({})
    expect(choicePayload(saved, 'pickup')).toEqual({ pickup_saved_address: 4 })
    expect(choiceProblems(emptyChoice(true)).savedId).toBeTruthy()
    const typed = {
      mode: 'typed',
      savedId: '',
      place: { name: 'A b', address: 'Abc', latitude: '', longitude: '' },
    }
    expect(choicePayload(typed, 'delivery')).toEqual({
      delivery: { name: 'A b', address: 'Abc', latitude: null, longitude: null },
    })
  })
})
