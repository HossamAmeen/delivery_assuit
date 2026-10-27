import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import TraderLocationsView from '@/views/TraderLocationsView.vue'
import { ApiError } from '@/api/http'
import * as locationsApi from '@/api/locations'
import { placePayload, placeProblems, placeToForm } from '@/utils/places'
import { plugins, signIn } from './helpers'

vi.mock('@/api/locations', async (orig) => ({
  ...(await orig()),
  listLocations: vi.fn(),
  createLocation: vi.fn(),
  updateLocation: vi.fn(),
  deleteLocation: vi.fn(),
}))

const ROWS = [
  {
    id: 2,
    name: 'Second',
    address: '2 Side St',
    latitude: 30.5,
    longitude: 31.5,
    is_pickup: true,
    is_delivery: true,
    is_default_pickup: false,
  },
  {
    id: 1,
    name: 'Main branch',
    address: '12 Nile St',
    latitude: null,
    longitude: null,
    is_pickup: true,
    is_delivery: false,
    is_default_pickup: true,
  },
]
const page = (results) => ({ count: results.length, next: null, previous: null, results })

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('trader')
  const w = mount(TraderLocationsView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
const fill = async (w, values) => {
  for (const [id, value] of Object.entries(values)) await w.find(`#loc-${id}`).setValue(value)
}

beforeEach(() => {
  vi.clearAllMocks()
  locationsApi.listLocations.mockResolvedValue(page(ROWS))
})

describe('trader locations list', () => {
  it('shows name, address and the pickup, delivery and default badges', async () => {
    const w = await open()
    const rows = w.findAll('[data-test="row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Second')
    expect(rows[0].find('[data-test="badge-delivery"]').exists()).toBe(true)
    expect(rows[0].find('[data-test="badge-default"]').exists()).toBe(false)
    expect(rows[1].find('[data-test="badge-default"]').exists()).toBe(true)
  })

  it('shows loading, empty, and error with retry', async () => {
    locationsApi.listLocations.mockResolvedValueOnce(page([]))
    let w = await open()
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
    locationsApi.listLocations.mockRejectedValueOnce(new ApiError({ status: 500 }))
    w = await open()
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })
})

describe('add and edit', () => {
  it('blocks an empty form and shows the field errors without calling the API', async () => {
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await w.find('[data-test="form"]').trigger('submit')
    expect(locationsApi.createLocation).not.toHaveBeenCalled()
    expect(w.find('#loc-name-error').exists()).toBe(true)
    expect(w.find('#loc-address-error').exists()).toBe(true)
  })

  it('creates with trimmed text, null coordinates, and the flags, then reloads', async () => {
    locationsApi.createLocation.mockResolvedValue({ id: 3 })
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await fill(w, { name: '  Branch 3 ', address: ' 9 Park Rd ' })
    await w.find('[data-test="is-delivery"]').setValue(true)
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(locationsApi.createLocation).toHaveBeenCalledWith({
      name: 'Branch 3',
      address: '9 Park Rd',
      latitude: null,
      longitude: null,
      is_pickup: true,
      is_delivery: true,
      is_default_pickup: false,
    })
    expect(locationsApi.listLocations).toHaveBeenCalledTimes(2)
    expect(w.find('[data-test="form"]').exists()).toBe(false)
  })

  it('sends coordinates as numbers', async () => {
    locationsApi.createLocation.mockResolvedValue({ id: 3 })
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await fill(w, {
      name: 'Branch',
      address: '9 Park Rd',
      latitude: '30.0444',
      longitude: '31.2357',
    })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    const body = locationsApi.createLocation.mock.calls[0][0]
    expect(body.latitude).toBe(30.0444)
    expect(body.longitude).toBe(31.2357)
  })

  it('rejects a lone coordinate and one out of range on the client', async () => {
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await fill(w, { name: 'Branch', address: '9 Park Rd', latitude: '30' })
    await w.find('[data-test="form"]').trigger('submit')
    expect(w.find('#loc-longitude-error').exists()).toBe(true)
    await fill(w, { latitude: '95', longitude: '10' })
    await w.find('[data-test="form"]').trigger('submit')
    expect(w.find('#loc-latitude-error').exists()).toBe(true)
    expect(locationsApi.createLocation).not.toHaveBeenCalled()
  })

  it('needs pickup or delivery', async () => {
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await fill(w, { name: 'Branch', address: '9 Park Rd' })
    await w.find('[data-test="is-pickup"]').setValue(false)
    await w.find('[data-test="form"]').trigger('submit')
    expect(w.find('[data-test="flags-error"]').exists()).toBe(true)
    expect(locationsApi.createLocation).not.toHaveBeenCalled()
  })

  it('shows server field errors on the matching field and keeps the values', async () => {
    locationsApi.createLocation.mockRejectedValue(
      new ApiError({ status: 400, errors: { address: ['Too short for the server.'] } }),
    )
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await fill(w, { name: 'Branch', address: '9 Park Rd' })
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('#loc-address-error').text()).toBe('Too short for the server.')
    expect(w.find('#loc-name').element.value).toBe('Branch')
  })

  it('edits a row with its values filled in and patches it', async () => {
    locationsApi.updateLocation.mockResolvedValue({ id: 2 })
    const w = await open()
    await w.findAll('[data-test="edit"]')[0].trigger('click')
    expect(w.find('#loc-name').element.value).toBe('Second')
    expect(w.find('#loc-latitude').element.value).toBe('30.5')
    await w.find('[data-test="is-default"]').setValue(true)
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    const [id, body] = locationsApi.updateLocation.mock.calls[0]
    expect(id).toBe(2)
    expect(body).toMatchObject({ is_default_pickup: true, is_pickup: true, is_delivery: true })
  })

  it('never sends the default flag for a delivery-only location', async () => {
    locationsApi.createLocation.mockResolvedValue({ id: 3 })
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await fill(w, { name: 'Drop', address: '9 Park Rd' })
    await w.find('[data-test="is-default"]').setValue(true)
    await w.find('[data-test="is-pickup"]').setValue(false)
    await w.find('[data-test="is-delivery"]').setValue(true)
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(locationsApi.createLocation.mock.calls[0][0].is_default_pickup).toBe(false)
  })

  it('disables the save button while the request runs', async () => {
    let resolve
    locationsApi.createLocation.mockReturnValue(new Promise((r) => (resolve = r)))
    const w = await open()
    await w.find('[data-test="add"]').trigger('click')
    await fill(w, { name: 'Branch', address: '9 Park Rd' })
    await w.find('[data-test="form"]').trigger('submit')
    expect(w.find('[data-test="save"]').attributes('disabled')).toBeDefined()
    resolve({ id: 1 })
    await flushPromises()
  })
})

describe('delete', () => {
  it('asks first, then deletes and reloads', async () => {
    locationsApi.deleteLocation.mockResolvedValue()
    const w = await open()
    await w.findAll('[data-test="delete"]')[0].trigger('click')
    expect(locationsApi.deleteLocation).not.toHaveBeenCalled()
    await w.find('[data-test="confirm-yes"]').trigger('click')
    await flushPromises()
    expect(locationsApi.deleteLocation).toHaveBeenCalledWith(2)
    expect(locationsApi.listLocations).toHaveBeenCalledTimes(2)
  })

  it('cancel keeps the row and calls nothing', async () => {
    const w = await open()
    await w.findAll('[data-test="delete"]')[0].trigger('click')
    await w.find('[data-test="confirm-no"]').trigger('click')
    expect(locationsApi.deleteLocation).not.toHaveBeenCalled()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('shows a friendly error if the delete fails', async () => {
    locationsApi.deleteLocation.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await open()
    await w.findAll('[data-test="delete"]')[0].trigger('click')
    await w.find('[data-test="confirm-yes"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="page-error"]').text()).toMatch(/went wrong/i)
  })
})

describe('place helpers and route', () => {
  it('placeToForm and placePayload round trip', () => {
    expect(placeToForm({ name: 'A', address: 'B', latitude: 1.5, longitude: null })).toEqual({
      name: 'A',
      address: 'B',
      latitude: '1.5',
      longitude: '',
    })
    expect(placePayload({ name: ' A ', address: ' B ', latitude: '', longitude: '' })).toEqual({
      name: 'A',
      address: 'B',
      latitude: null,
      longitude: null,
    })
  })

  it('placeProblems accepts a valid place', () => {
    expect(
      placeProblems({ name: 'Ab', address: 'Abc', latitude: '-90', longitude: '180' }),
    ).toEqual({})
  })

  it('the route is a trader-only child', () => {
    const trader = routes.find((r) => r.path === '/trader')
    const child = trader.children.find((c) => c.name === 'trader-locations')
    expect(child.component).toBe(TraderLocationsView)
    setActivePinia(createPinia())
    signIn('client')
    expect(authGuard({ meta: trader.meta })).not.toBe(true)
  })
})
