import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import ApprovalsView from '@/views/ApprovalsView.vue'
import LoginView from '@/views/LoginView.vue'
import { ApiError } from '@/api/http'
import * as usersApi from '@/api/users'
import * as authApi from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { plugins, signIn } from './helpers'

vi.mock('@/api/users', async (orig) => ({
  ...(await orig()),
  listUsers: vi.fn(),
  approveUser: vi.fn(),
  rejectUser: vi.fn(),
}))
vi.mock('@/api/auth', async (orig) => ({ ...(await orig()), login: vi.fn() }))

const PENDING = [
  {
    id: 5,
    full_name: 'Omar Driver',
    phone: '01011112222',
    email: 'o@x.com',
    role: 'driver',
    status: 'pending_approval',
  },
  {
    id: 6,
    full_name: 'Sara Shop',
    phone: '01022223333',
    email: '',
    role: 'trader',
    status: 'pending_approval',
  },
]
async function open(role = 'admin') {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  return mount(ApprovalsView, { global: { plugins: plugins([router], pinia) } })
}
beforeEach(() => {
  vi.clearAllMocks()
  usersApi.listUsers.mockResolvedValue({
    count: 2,
    next: null,
    previous: null,
    results: [...PENDING],
  })
})

describe('approvals queue', () => {
  it('loads only pending accounts and shows name, role, phone and email', async () => {
    const w = await open()
    expect(w.find('[data-test="loading"]').exists()).toBe(true)
    await flushPromises()
    expect(usersApi.listUsers).toHaveBeenCalledWith({ status: 'pending_approval', page_size: 100 })
    const rows = w.findAll('[data-test="row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Omar Driver')
    expect(rows[0].text()).toContain('Driver')
    expect(rows[0].text()).toContain('01011112222')
    expect(rows[0].text()).toContain('o@x.com')
  })

  it('approve calls the endpoint and removes the row', async () => {
    usersApi.approveUser.mockResolvedValue({})
    const w = await open('manager')
    await flushPromises()
    await w.findAll('[data-test="approve"]')[0].trigger('click')
    await flushPromises()
    expect(usersApi.approveUser).toHaveBeenCalledWith(5)
    expect(w.findAll('[data-test="row"]')).toHaveLength(1)
  })

  it('reject with a reason sends it trimmed, and removes the row', async () => {
    usersApi.rejectUser.mockResolvedValue({})
    const w = await open()
    await flushPromises()
    await w.findAll('[data-test="reject"]')[0].trigger('click')
    await w.find('#reason-5').setValue('  Missing documents ')
    await w.find('[data-test="confirm-reject"]').trigger('click')
    await flushPromises()
    expect(usersApi.rejectUser).toHaveBeenCalledWith(5, 'Missing documents')
    expect(w.findAll('[data-test="row"]')).toHaveLength(1)
  })

  it('reject can be sent with an empty reason', async () => {
    usersApi.rejectUser.mockResolvedValue({})
    const w = await open()
    await flushPromises()
    await w.findAll('[data-test="reject"]')[1].trigger('click')
    await w.find('[data-test="confirm-reject"]').trigger('click')
    await flushPromises()
    expect(usersApi.rejectUser).toHaveBeenCalledWith(6, '')
  })

  it('keeps the row and shows the server error when an action fails', async () => {
    usersApi.approveUser.mockRejectedValue(
      new ApiError({ status: 400, message: 'Validation failed.' }),
    )
    const w = await open()
    await flushPromises()
    await w.findAll('[data-test="approve"]')[0].trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toBe('Validation failed.')
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('shows a message, not a blank page, when nothing is pending', async () => {
    usersApi.listUsers.mockResolvedValue({ count: 0, next: null, previous: null, results: [] })
    const w = await open()
    await flushPromises()
    expect(w.find('[data-test="empty"]').text()).toBe('No registrations are waiting for approval.')
  })

  it('shows an error with retry when loading fails', async () => {
    usersApi.listUsers.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    await flushPromises()
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })
})

describe('approvals route', () => {
  const to = { meta: { roles: ['admin', 'manager'] } }
  it.each([
    ['admin', true],
    ['manager', true],
    ['driver', '/driver'],
    ['trader', '/trader'],
    ['client', '/client'],
  ])('%s -> %s', (role, expected) => {
    setActivePinia(createPinia())
    signIn(role)
    expect(authGuard(to)).toBe(expected)
  })

  it('is registered under the admin area', () => {
    const admin = routes.find((r) => r.path === '/admin')
    expect(admin.children.map((c) => c.name)).toContain('approvals')
    expect(admin.meta.roles).toEqual(['admin', 'manager'])
  })
})

describe('rejected login', () => {
  it('shows the server message (with the reason) and stays on login', async () => {
    authApi.login.mockRejectedValue(
      new ApiError({
        status: 403,
        code: 'account_rejected',
        message: 'Your registration was rejected. Reason: Bad photo.',
      }),
    )
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().status = 'anonymous'
    router.push('/login')
    await router.isReady()
    const w = mount(LoginView, { global: { plugins: plugins([router], pinia) } })
    await w.find('#login-identifier').setValue('0100')
    await w.find('#login-password').setValue('pw')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').text()).toBe(
      'Your registration was rejected. Reason: Bad photo.',
    )
    expect(router.currentRoute.value.name).toBe('login')
    expect(useAuthStore().isAuthenticated).toBe(false)
  })

  it('falls back to a local message when the server text is empty', async () => {
    authApi.login.mockRejectedValue(new ApiError({ status: 403, code: 'account_rejected' }))
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().status = 'anonymous'
    router.push('/login')
    await router.isReady()
    const w = mount(LoginView, { global: { plugins: plugins([router], pinia) } })
    await w.find('#login-identifier').setValue('0100')
    await w.find('#login-password').setValue('pw')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').text()).toBe('Your registration was rejected.')
  })
})
