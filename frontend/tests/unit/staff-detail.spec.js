import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import StaffDetailView from '@/views/StaffDetailView.vue'
import { ApiError } from '@/api/http'
import * as staffApi from '@/api/staff'
import * as usersApi from '@/api/users'
import { plugins, signIn } from './helpers'

vi.mock('@/api/staff', async (orig) => ({
  ...(await orig()),
  getStaff: vi.fn(),
  setItemPrice: vi.fn(),
}))
vi.mock('@/api/users', async (orig) => ({
  ...(await orig()),
  approveUser: vi.fn(),
  activateUser: vi.fn(),
  deactivateUser: vi.fn(),
}))

const user = (role, status = 'active') => ({
  id: 5,
  full_name: 'Test Person',
  phone: '01000000030',
  email: '',
  role,
  status,
})
const RECENT = [{ id: 12, reference: 'ORD-000012', status: 'delivered' }]
const DRIVER = {
  user: user('driver'),
  orders_total: 5,
  delivered_orders: 4,
  cancelled_orders: 1,
  active_order_reference: 'ORD-000013',
  recent_orders: RECENT,
}
const TRADER = {
  user: user('trader'),
  orders_total: 2,
  shop: { id: 1, name: 'Alpha Grill', is_available: true },
  locations: [{ id: 1, name: 'Main', address: '12 Nile St' }],
  items: [
    { id: 7, name: 'Pie', is_hidden: false, price: 9.5 },
    { id: 8, name: 'Wrap', is_hidden: true, price: null },
  ],
  recent_orders: RECENT,
}
const CLIENT = { user: user('client'), orders_total: 0, recent_orders: [] }

async function open(kind, payload) {
  staffApi.getStaff.mockResolvedValue(structuredClone(payload))
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('admin')
  router.push(`/admin/${kind}/5`)
  await router.isReady()
  const w = mount(StaffDetailView, {
    props: { kind },
    global: { plugins: plugins([router], pinia) },
  })
  await flushPromises()
  return w
}

beforeEach(() => vi.clearAllMocks())

describe('staff details', () => {
  it('driver: profile, performance, active order and recent orders', async () => {
    const w = await open('drivers', DRIVER)
    expect(staffApi.getStaff).toHaveBeenCalledWith('drivers', '5')
    expect(w.find('[data-test="name"]').text()).toBe('Test Person')
    expect(w.find('[data-test="delivered"]').text()).toBe('4')
    expect(w.find('[data-test="cancelled"]').text()).toBe('1')
    expect(w.find('[data-test="active-order"]').text()).toBe('ORD-000013')
    expect(w.find('[data-test="order"] a').attributes('href')).toBe('/admin/orders/12')
  })

  it('client: orders and an empty state', async () => {
    const w = await open('clients', CLIENT)
    expect(w.find('[data-test="no-orders"]').exists()).toBe(true)
    expect(w.find('[data-test="delivered"]').exists()).toBe(false)
  })

  it('shows the action that matches the status', async () => {
    let w = await open('drivers', { ...DRIVER, user: user('driver', 'pending_approval') })
    expect(w.find('[data-test="approve"]').exists()).toBe(true)
    expect(w.find('[data-test="deactivate"]').exists()).toBe(false)
    w = await open('drivers', DRIVER)
    expect(w.find('[data-test="deactivate"]').exists()).toBe(true)
    w = await open('drivers', { ...DRIVER, user: user('driver', 'deactivated') })
    expect(w.find('[data-test="activate"]').exists()).toBe(true)
    w = await open('drivers', { ...DRIVER, user: user('driver', 'rejected') })
    expect(w.find('[data-test="approve"]').exists()).toBe(false)
  })

  it('a pending client has no approve action (clients are active at once)', async () => {
    const w = await open('clients', { ...CLIENT, user: user('client', 'pending_approval') })
    expect(w.find('[data-test="approve"]').exists()).toBe(false)
  })

  it('approve updates the status shown', async () => {
    usersApi.approveUser.mockResolvedValue({ status: 'active' })
    const w = await open('drivers', { ...DRIVER, user: user('driver', 'pending_approval') })
    await w.find('[data-test="approve"]').trigger('click')
    await flushPromises()
    expect(usersApi.approveUser).toHaveBeenCalledWith(5)
    expect(w.find('[data-test="status"]').text()).toBe('Active')
    expect(w.find('[data-test="deactivate"]').exists()).toBe(true)
  })

  it('deactivate and activate call the right endpoints; a failure is friendly', async () => {
    usersApi.deactivateUser.mockResolvedValue({ status: 'deactivated' })
    const w = await open('drivers', DRIVER)
    await w.find('[data-test="deactivate"]').trigger('click')
    expect(usersApi.deactivateUser).not.toHaveBeenCalled()
    await w.find('[data-test="confirm-deactivate"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="status"]').text()).toBe('Deactivated')
    usersApi.activateUser.mockRejectedValue(new ApiError({ status: 500 }))
    await w.find('[data-test="activate"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toMatch(/went wrong/i)
    expect(w.find('[data-test="status"]').text()).toBe('Deactivated')
  })

  it('trader: shop, locations, items and orders', async () => {
    const w = await open('traders', TRADER)
    expect(w.find('[data-test="shop"]').text()).toContain('Alpha Grill')
    expect(w.findAll('[data-test="location"]')).toHaveLength(1)
    expect(w.findAll('[data-test="item"]')).toHaveLength(2)
    expect(w.find('[data-test="price-7"]').element.value).toBe('9.5')
    expect(w.find('[data-test="price-8"]').element.value).toBe('')
  })

  it('trader without a shop says so', async () => {
    const w = await open('traders', { ...TRADER, shop: null, items: [], locations: [] })
    expect(w.find('[data-test="no-shop"]').exists()).toBe(true)
    expect(w.find('[data-test="no-items"]').exists()).toBe(true)
  })

  it('sets, changes and clears an item price', async () => {
    staffApi.setItemPrice.mockImplementation(async (id, price) => ({ id, price }))
    const w = await open('traders', TRADER)
    await w.find('[data-test="price-8"]').setValue(' 12.5 ')
    await w.find('[data-test="save-price-8"]').trigger('click')
    await flushPromises()
    expect(staffApi.setItemPrice).toHaveBeenCalledWith(8, 12.5)
    await w.find('[data-test="price-7"]').setValue('')
    await w.find('[data-test="save-price-7"]').trigger('click')
    await flushPromises()
    expect(staffApi.setItemPrice).toHaveBeenCalledWith(7, null)
    expect(w.find('[data-test="notice"]').exists()).toBe(true)
  })

  it.each(['abc', '-1', '100001', '1.234'])('blocks a bad price (%s)', async (bad) => {
    const w = await open('traders', TRADER)
    await w.find('[data-test="price-7"]').setValue(bad)
    await w.find('[data-test="save-price-7"]').trigger('click')
    expect(staffApi.setItemPrice).not.toHaveBeenCalled()
    expect(w.find('[data-test="price-error"]').exists()).toBe(true)
  })

  it('shows a server price error on the field and keeps the typed value', async () => {
    staffApi.setItemPrice.mockRejectedValue(
      new ApiError({ status: 400, errors: { price: ['Server: bad price.'] } }),
    )
    const w = await open('traders', TRADER)
    await w.find('[data-test="price-7"]').setValue('5')
    await w.find('[data-test="save-price-7"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="price-error"]').text()).toBe('Server: bad price.')
    expect(w.find('[data-test="price-7"]').element.value).toBe('5')
  })

  it('says not found on a 404, and shows retry on errors', async () => {
    staffApi.getStaff.mockRejectedValueOnce(new ApiError({ status: 404 }))
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    signIn('admin')
    router.push('/admin/drivers/5')
    await router.isReady()
    const w = mount(StaffDetailView, {
      props: { kind: 'drivers' },
      global: { plugins: plugins([router], pinia) },
    })
    await flushPromises()
    expect(w.find('[data-test="missing"]').exists()).toBe(true)
  })

  it('has one detail route per kind', () => {
    const admin = routes.find((r) => r.path === '/admin')
    for (const kind of ['drivers', 'traders', 'clients']) {
      const r = admin.children.find((c) => c.path.startsWith(`${kind}/:id`))
      expect(r.component).toBe(StaffDetailView)
      expect(r.props).toEqual({ kind })
    }
  })
})

describe('deactivate asks first (BL-068)', () => {
  it('keep closes the question and calls nothing', async () => {
    const w = await open('drivers', DRIVER)
    await w.find('[data-test="deactivate"]').trigger('click')
    expect(w.find('[data-test="confirm-box"]').exists()).toBe(true)
    await w.find('[data-test="keep"]').trigger('click')
    expect(usersApi.deactivateUser).not.toHaveBeenCalled()
    expect(w.find('[data-test="deactivate"]').exists()).toBe(true)
  })

  it('approve and activate need no confirmation', async () => {
    usersApi.approveUser.mockResolvedValue({ status: 'active' })
    const w = await open('drivers', { ...DRIVER, user: user('driver', 'pending_approval') })
    await w.find('[data-test="approve"]').trigger('click')
    await flushPromises()
    expect(usersApi.approveUser).toHaveBeenCalledTimes(1)
  })
})
