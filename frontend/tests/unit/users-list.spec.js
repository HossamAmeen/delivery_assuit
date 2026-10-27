import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import UsersListView from '@/views/UsersListView.vue'
import { ApiError } from '@/api/http'
import * as usersApi from '@/api/users'
import http from '@/api/http'
import { plugins, signIn } from './helpers'

vi.mock('@/api/users', async (orig) => ({
  ...(await orig()),
  listUsers: vi.fn(),
  activateUser: vi.fn(),
  deactivateUser: vi.fn(),
}))

const row = (id, role, status, name = `User ${id}`) => ({
  id,
  full_name: name,
  phone: `0100000000${id}`,
  username: null,
  email: '',
  role,
  status,
})
const ROWS = [
  row(2, 'admin', 'active', 'Boss'),
  row(3, 'driver', 'active', 'Driver Dan'),
  row(4, 'client', 'deactivated', 'Client Cy'),
  row(5, 'trader', 'pending_approval', 'Trader Tim'),
]
const PAGE = { count: 4, next: null, previous: null, results: ROWS }

async function open(role = 'admin') {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  const w = mount(UsersListView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
beforeEach(() => {
  vi.clearAllMocks()
  usersApi.listUsers.mockResolvedValue(PAGE)
})
afterEach(() => vi.useRealTimers())

describe('users list', () => {
  it('loads with page 1 and no filters, and shows name, phone, role, status', async () => {
    const w = await open()
    expect(usersApi.listUsers).toHaveBeenCalledWith({ page: 1, role: '', status: '', search: '' })
    const first = w.findAll('[data-test="row"]')[1]
    expect(first.text()).toContain('Driver Dan')
    expect(first.text()).toContain('Driver')
    expect(first.text()).toContain('Active')
    expect(w.findAll('[data-test="row"]')).toHaveLength(4)
  })

  it('rows link to the detail route', async () => {
    const w = await open()
    expect(w.findAll('[data-test="open"]')[1].attributes('href')).toBe('/admin/users/3')
  })

  it('sends role, status and search to the API and returns to page 1', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const w = await open()
    await w.find('[data-test="role-filter"]').setValue('driver')
    await w.find('[data-test="status-filter"]').setValue('active')
    await w.find('[data-test="search"]').setValue('  dan ')
    vi.advanceTimersByTime(300)
    await flushPromises()
    const last = usersApi.listUsers.mock.calls.at(-1)[0]
    expect(last).toEqual({ page: 1, role: 'driver', status: 'active', search: 'dan' })
  })

  it('pages with next and previous', async () => {
    usersApi.listUsers.mockResolvedValue({ ...PAGE, count: 45, next: 'x', previous: null })
    const w = await open()
    expect(w.find('[data-test="prev"]').attributes('disabled')).toBeDefined()
    await w.find('[data-test="next"]').trigger('click')
    await flushPromises()
    expect(usersApi.listUsers.mock.calls.at(-1)[0].page).toBe(2)
    expect(w.find('[data-test="page"]').text()).toContain('Page 2')
  })

  it('activate and deactivate call the endpoints and update the row status', async () => {
    usersApi.deactivateUser.mockResolvedValue({ status: 'deactivated' })
    usersApi.activateUser.mockResolvedValue({ status: 'active' })
    const w = await open()
    const rows = w.findAll('[data-test="row"]')
    await rows[1].find('[data-test="deactivate"]').trigger('click')
    expect(usersApi.deactivateUser).not.toHaveBeenCalled()
    await rows[1].find('[data-test="confirm-deactivate"]').trigger('click')
    await flushPromises()
    expect(usersApi.deactivateUser).toHaveBeenCalledWith(3)
    expect(rows[1].find('[data-test="status"]').text()).toBe('Deactivated')
    await rows[2].find('[data-test="activate"]').trigger('click')
    await flushPromises()
    expect(usersApi.activateUser).toHaveBeenCalledWith(4)
    expect(rows[2].find('[data-test="status"]').text()).toBe('Active')
  })

  it('shows buttons only for the matching status; pending has none', async () => {
    const w = await open()
    const rows = w.findAll('[data-test="row"]')
    expect(rows[1].find('[data-test="activate"]').exists()).toBe(false)
    expect(rows[2].find('[data-test="deactivate"]').exists()).toBe(false)
    expect(rows[3].findAll('button')).toHaveLength(0)
  })

  it('a Manager sees no actions on an Admin row and never calls the API for it', async () => {
    const w = await open('manager')
    const adminRow = w.findAll('[data-test="row"]')[0]
    expect(adminRow.findAll('button')).toHaveLength(0)
    expect(w.findAll('[data-test="row"]')[1].find('[data-test="deactivate"]').exists()).toBe(true)
    expect(usersApi.deactivateUser).not.toHaveBeenCalled()
  })

  it('an Admin does see actions on another Admin', async () => {
    const w = await open('admin')
    expect(w.findAll('[data-test="row"]')[0].find('[data-test="deactivate"]').exists()).toBe(true)
  })

  it('shows the server 403 message if a click still fails', async () => {
    usersApi.deactivateUser.mockRejectedValue(
      new ApiError({
        status: 403,
        message: 'You cannot manage an administrator account.',
        code: 'admin_protected',
      }),
    )
    const w = await open('admin')
    const row = w.findAll('[data-test="row"]')[1]
    await row.find('[data-test="deactivate"]').trigger('click')
    await row.find('[data-test="confirm-deactivate"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toBe(
      'You cannot manage an administrator account.',
    )
    expect(w.findAll('[data-test="row"]')[1].find('[data-test="status"]').text()).toBe('Active')
  })

  it('shows empty and error-with-retry states', async () => {
    usersApi.listUsers.mockResolvedValueOnce({ count: 0, next: null, previous: null, results: [] })
    let w = await open()
    expect(w.find('[data-test="empty"]').text()).toBe('No users match these filters.')
    usersApi.listUsers.mockRejectedValueOnce(new ApiError({ status: 500 }))
    w = await open()
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(4)
  })
})

describe('users route', () => {
  it('is an admin-area child and blocked for other roles', () => {
    const admin = routes.find((r) => r.path === '/admin')
    expect(admin.children.map((c) => c.name)).toContain('users')
    for (const role of ['driver', 'trader', 'client']) {
      setActivePinia(createPinia())
      signIn(role)
      expect(authGuard({ meta: admin.meta })).not.toBe(true)
    }
  })
})

describe('listUsers query building', () => {
  it('omits empty filters from the request', async () => {
    const real = await vi.importActual('@/api/users')
    const spy = vi.spyOn(http, 'get').mockResolvedValue({ data: { data: PAGE } })
    await real.listUsers({ page: 2, role: '', status: 'active', search: '' })
    expect(spy).toHaveBeenCalledWith('users/', { params: { page: 2, status: 'active' } })
    spy.mockRestore()
  })
})

describe('deactivate asks first (BL-068)', () => {
  it('keep closes the question and calls nothing', async () => {
    const w = await open()
    const row = w.findAll('[data-test="row"]')[1]
    await row.find('[data-test="deactivate"]').trigger('click')
    await row.find('[data-test="keep"]').trigger('click')
    expect(usersApi.deactivateUser).not.toHaveBeenCalled()
    expect(row.find('[data-test="deactivate"]').exists()).toBe(true)
  })
})
