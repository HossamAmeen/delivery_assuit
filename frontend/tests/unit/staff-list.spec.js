import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import StaffListView from '@/views/StaffListView.vue'
import { ApiError } from '@/api/http'
import * as staffApi from '@/api/staff'
import { plugins, signIn } from './helpers'

vi.mock('@/api/staff', async (orig) => ({ ...(await orig()), listStaff: vi.fn() }))

const DRIVERS = [
  { id: 5, full_name: 'Ali Driver', phone: '01000000030', status: 'active', delivered_orders: 4 },
  {
    id: 6,
    full_name: 'New Driver',
    phone: '01000000031',
    status: 'pending_approval',
    delivered_orders: 0,
  },
]
const TRADERS = [
  {
    id: 7,
    full_name: 'Tarek',
    phone: '01000000010',
    status: 'active',
    shop_name: 'Alpha Grill',
    shop_phone: '',
    orders: 9,
  },
  {
    id: 8,
    full_name: 'Newbie',
    phone: '01000000011',
    status: 'pending_approval',
    shop_name: '',
    shop_phone: '',
    orders: 0,
  },
]
const CLIENTS = [{ id: 9, full_name: 'Mona', phone: '01000000020', status: 'active', orders: 3 }]
const page = (results, extra = {}) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
  ...extra,
})

async function open(kind) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('manager')
  const w = mount(StaffListView, { props: { kind }, global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  staffApi.listStaff.mockImplementation(async (kind) =>
    page(structuredClone({ drivers: DRIVERS, traders: TRADERS, clients: CLIENTS }[kind])),
  )
})
afterEach(() => vi.useRealTimers())

describe('staff lists', () => {
  it('drivers: name, phone, status, delivered orders, link to details', async () => {
    const w = await open('drivers')
    const rows = w.findAll('[data-test="row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].find('[data-test="count"]').text()).toBe('4')
    expect(rows[1].find('[data-test="status"]').text()).toBe('Pending approval')
    expect(rows[0].find('[data-test="open"]').attributes('href')).toBe('/admin/drivers/5')
    expect(staffApi.listStaff.mock.calls[0][0]).toBe('drivers')
  })

  it('traders: shop name column and order count', async () => {
    const w = await open('traders')
    const rows = w.findAll('[data-test="row"]')
    expect(rows[0].find('[data-test="shop"]').text()).toBe('Alpha Grill')
    expect(rows[1].find('[data-test="shop"]').text()).toBe('—')
    expect(rows[0].find('[data-test="count"]').text()).toBe('9')
  })

  it('clients: no shop column, order count', async () => {
    const w = await open('clients')
    expect(w.find('[data-test="shop"]').exists()).toBe(false)
    expect(w.find('[data-test="count"]').text()).toBe('3')
    expect(w.find('[data-test="open"]').attributes('href')).toBe('/admin/clients/9')
  })

  it('searches and filters by status after a short pause, from page 1', async () => {
    const w = await open('drivers')
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    await w.find('[data-test="search"]').setValue('  ali ')
    await w.find('[data-test="status-filter"]').setValue('pending_approval')
    vi.advanceTimersByTime(300)
    await flushPromises()
    expect(staffApi.listStaff.mock.calls.at(-1)).toEqual([
      'drivers',
      { page: 1, status: 'pending_approval', search: 'ali' },
    ])
  })

  it('pages, shows empty, and error with retry', async () => {
    staffApi.listStaff.mockResolvedValueOnce(page(structuredClone(CLIENTS), { next: 'x' }))
    let w = await open('clients')
    await w.find('[data-test="next"]').trigger('click')
    await flushPromises()
    expect(staffApi.listStaff.mock.calls.at(-1)[1].page).toBe(2)
    staffApi.listStaff.mockResolvedValueOnce(page([]))
    w = await open('drivers')
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
    staffApi.listStaff.mockRejectedValueOnce(new ApiError({ status: 500 }))
    w = await open('drivers')
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('has one route per kind for staff', () => {
    const admin = routes.find((r) => r.path === '/admin')
    for (const kind of ['drivers', 'traders', 'clients']) {
      const route = admin.children.find((c) => c.name === `staff-${kind}`)
      expect(route.component).toBe(StaffListView)
      expect(route.props).toEqual({ kind })
    }
  })
})
