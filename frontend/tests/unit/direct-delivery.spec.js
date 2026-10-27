import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import DirectDeliveryView from '@/views/DirectDeliveryView.vue'
import { ApiError } from '@/api/http'
import * as ordersApi from '@/api/orders'
import * as addressesApi from '@/api/addresses'
import { plugins, signIn } from './helpers'

vi.mock('@/api/orders', async (orig) => ({ ...(await orig()), createOrder: vi.fn() }))
vi.mock('@/api/addresses', async (orig) => ({ ...(await orig()), listAddresses: vi.fn() }))

const ADDRESSES = [
  { id: 4, name: 'Home', address: '5 Garden St' },
  { id: 5, name: 'Work', address: '2 Side St' },
]
const CREATED = { id: 20, reference: 'ORD-000020', status: 'created' }

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  const w = mount(DirectDeliveryView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
const type = async (w, prefix, values) => {
  for (const [id, v] of Object.entries(values)) await w.find(`#${prefix}-${id}`).setValue(v)
}
const fillAll = async (w) => {
  await type(w, 'dir-pick', { name: 'Office', address: '1 Tahrir Sq' })
  await type(w, 'dir-del', { name: 'Mum', address: '9 Rose St' })
  await w.find('#dir-description').setValue('  A box of documents ')
}

beforeEach(() => {
  vi.clearAllMocks()
  addressesApi.listAddresses.mockResolvedValue({ results: [] })
})

describe('direct delivery', () => {
  it('requires pickup, delivery and details, and calls nothing while invalid', async () => {
    const w = await open()
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.createOrder).not.toHaveBeenCalled()
    expect(w.find('#dir-pick-name-error').exists()).toBe(true)
    expect(w.find('#dir-pick-address-error').exists()).toBe(true)
    expect(w.find('#dir-del-name-error').exists()).toBe(true)
    expect(w.find('[data-test="description-error"]').exists()).toBe(true)
  })

  it('rejects details shorter than 3 characters', async () => {
    const w = await open()
    await fillAll(w)
    await w.find('#dir-description').setValue('ab')
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.createOrder).not.toHaveBeenCalled()
  })

  it('creates the order with typed places and shows the reference', async () => {
    ordersApi.createOrder.mockResolvedValue(CREATED)
    const w = await open()
    await fillAll(w)
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(ordersApi.createOrder).toHaveBeenCalledWith({
      pickup: { name: 'Office', address: '1 Tahrir Sq', latitude: null, longitude: null },
      delivery: { name: 'Mum', address: '9 Rose St', latitude: null, longitude: null },
      description: 'A box of documents',
    })
    expect(w.find('[data-test="reference"]').text()).toBe('ORD-000020')
  })

  it('can use saved addresses for both sides', async () => {
    addressesApi.listAddresses.mockResolvedValue({ results: ADDRESSES })
    ordersApi.createOrder.mockResolvedValue(CREATED)
    const w = await open()
    await w.find('[data-test="dir-pick-saved"]').setValue('4')
    await w.find('[data-test="dir-del-saved"]').setValue('5')
    await w.find('#dir-description').setValue('Keys')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(ordersApi.createOrder).toHaveBeenCalledWith({
      pickup_saved_address: 4,
      delivery_saved_address: 5,
      description: 'Keys',
    })
  })

  it('mixes a saved delivery with a typed pickup', async () => {
    addressesApi.listAddresses.mockResolvedValue({ results: ADDRESSES })
    ordersApi.createOrder.mockResolvedValue(CREATED)
    const w = await open()
    await w.find('[data-test="dir-pick-mode-typed"]').setValue(true)
    await type(w, 'dir-pick', { name: 'Office', address: '1 Tahrir Sq' })
    await w.find('[data-test="dir-del-saved"]').setValue('5')
    await w.find('#dir-description').setValue('Keys')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    const body = ordersApi.createOrder.mock.calls[0][0]
    expect(body.pickup.name).toBe('Office')
    expect(body.delivery_saved_address).toBe(5)
  })

  it('shows server errors on the right side and keeps the typed values', async () => {
    ordersApi.createOrder.mockRejectedValue(
      new ApiError({
        status: 400,
        errors: {
          pickup: { address: ['Server: pickup address.'] },
          description: ['Server: details.'],
        },
      }),
    )
    const w = await open()
    await fillAll(w)
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('#dir-pick-address-error').text()).toBe('Server: pickup address.')
    expect(w.find('[data-test="description-error"]').text()).toBe('Server: details.')
    expect(w.find('#dir-del-address').element.value).toBe('9 Rose St')
  })

  it('shows a friendly message and keeps the form on a server crash', async () => {
    ordersApi.createOrder.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await open()
    await fillAll(w)
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').text()).toMatch(/went wrong/i)
    expect(w.find('#dir-description').element.value).toBe('  A box of documents ')
  })

  it('does not submit twice while the request runs', async () => {
    let resolve
    ordersApi.createOrder.mockReturnValue(new Promise((r) => (resolve = r)))
    const w = await open()
    await fillAll(w)
    await w.find('[data-test="form"]').trigger('submit')
    await w.find('[data-test="form"]').trigger('submit')
    expect(ordersApi.createOrder).toHaveBeenCalledTimes(1)
    resolve(CREATED)
    await flushPromises()
  })

  it('is a client-only route', () => {
    const client = routes.find((r) => r.path === '/client')
    expect(client.children.find((c) => c.name === 'client-direct').component).toBe(
      DirectDeliveryView,
    )
  })
})
