import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import ClientAddressesView from '@/views/ClientAddressesView.vue'
import { ApiError } from '@/api/http'
import * as addressesApi from '@/api/addresses'
import { plugins, signIn } from './helpers'

vi.mock('@/api/addresses', async (orig) => ({
  ...(await orig()),
  listAddresses: vi.fn(),
  createAddress: vi.fn(),
  updateAddress: vi.fn(),
  deleteAddress: vi.fn(),
}))

const ROWS = [
  { id: 2, name: 'Work', address: '2 Side St', latitude: 30.5, longitude: 31.5 },
  { id: 1, name: 'Home', address: '5 Garden St', latitude: null, longitude: null },
]
const page = (results) => ({ count: results.length, next: null, previous: null, results })

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('client')
  const w = mount(ClientAddressesView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
const fill = async (w, values) => {
  for (const [id, value] of Object.entries(values)) await w.find(`#addr-${id}`).setValue(value)
}

beforeEach(() => {
  vi.clearAllMocks()
  addressesApi.listAddresses.mockResolvedValue(page(ROWS))
})

describe('saved addresses', () => {
  it('lists name and address, with edit and delete', async () => {
    const w = await open()
    const rows = w.findAll('[data-test="row"]')
    expect(rows).toHaveLength(2)
    expect(rows[1].text()).toContain('Home')
    expect(rows[1].text()).toContain('5 Garden St')
  })

  it('shows the empty state and an error with retry', async () => {
    addressesApi.listAddresses.mockResolvedValueOnce(page([]))
    let w = await open()
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
    addressesApi.listAddresses.mockRejectedValueOnce(new ApiError({ isNetworkError: true }))
    w = await open()
    expect(w.find('[data-test="load-error"]').text()).toContain('offline')
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('has no pickup or delivery options', async () => {
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    expect(w.findAll('input').map((i) => i.attributes('name'))).toEqual([
      'name',
      'address',
      'latitude',
      'longitude',
    ])
  })

  it('blocks an invalid form, then creates with the trimmed payload and reloads', async () => {
    addressesApi.createAddress.mockResolvedValue({ id: 3 })
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await w.find('[data-test="form"]').trigger('submit')
    expect(addressesApi.createAddress).not.toHaveBeenCalled()
    expect(w.find('#addr-name-error').exists()).toBe(true)
    await fill(w, { name: ' Mum ', address: ' 1 Rose St ', latitude: '30.1', longitude: '31.2' })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(addressesApi.createAddress).toHaveBeenCalledWith({
      name: 'Mum',
      address: '1 Rose St',
      latitude: 30.1,
      longitude: 31.2,
    })
    expect(addressesApi.listAddresses).toHaveBeenCalledTimes(2)
  })

  it('shows server errors on the field and keeps typed values', async () => {
    addressesApi.createAddress.mockRejectedValue(
      new ApiError({ status: 400, errors: { non_field_errors: ['x'], name: ['Server no.'] } }),
    )
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await fill(w, { name: 'Mum', address: '1 Rose St' })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('#addr-name-error').text()).toBe('Server no.')
    expect(w.find('#addr-address').element.value).toBe('1 Rose St')
  })

  it('edits with the values filled in', async () => {
    addressesApi.updateAddress.mockResolvedValue({ id: 2 })
    const w = await open()
    await w.findAll('[data-test="edit"]')[0].trigger('click')
    expect(w.find('#addr-name').element.value).toBe('Work')
    await fill(w, { name: 'Office' })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(addressesApi.updateAddress).toHaveBeenCalledWith(2, {
      name: 'Office',
      address: '2 Side St',
      latitude: 30.5,
      longitude: 31.5,
    })
  })

  it('asks before deleting and removes the row', async () => {
    addressesApi.deleteAddress.mockResolvedValue()
    const w = await open()
    await w.findAll('[data-test="delete"]')[0].trigger('click')
    expect(addressesApi.deleteAddress).not.toHaveBeenCalled()
    await w.find('[data-test="confirm-yes"]').trigger('click')
    await flushPromises()
    expect(addressesApi.deleteAddress).toHaveBeenCalledWith(2)
    expect(w.findAll('[data-test="row"]')).toHaveLength(1)
  })

  it('shows a friendly error when the delete fails', async () => {
    addressesApi.deleteAddress.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await open()
    await w.findAll('[data-test="delete"]')[0].trigger('click')
    await w.find('[data-test="confirm-yes"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="page-error"]').text()).toMatch(/went wrong/i)
  })

  it('is a client-only route', () => {
    const client = routes.find((r) => r.path === '/client')
    expect(client.children.find((c) => c.name === 'client-addresses').component).toBe(
      ClientAddressesView,
    )
    setActivePinia(createPinia())
    signIn('trader')
    expect(authGuard({ meta: client.meta })).not.toBe(true)
  })
})
