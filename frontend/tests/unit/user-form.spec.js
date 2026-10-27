import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import UserFormView from '@/views/UserFormView.vue'
import { ApiError } from '@/api/http'
import * as usersApi from '@/api/users'
import { plugins, signIn } from './helpers'

vi.mock('@/api/users', async (orig) => ({
  ...(await orig()),
  getUser: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
}))

const TARGET = {
  id: 9,
  full_name: 'Omar Khaled',
  phone: '01011112222',
  username: null,
  email: 'o@x.com',
  role: 'driver',
  status: 'rejected',
  rejection_reason: 'Bad photo',
  last_action: {
    action: 'rejected',
    reason: 'Bad photo',
    actor_id: 1,
    actor_name: 'Demo Admin',
    created_at: '2026-10-26T12:00:00Z',
  },
}
let router
async function open(path, role = 'admin') {
  router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role) // the signed-in user has id 1
  router.push(path)
  await router.isReady()
  const w = mount(UserFormView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}
const roleValues = (w) => w.findAll('#uf-role option').map((o) => o.attributes('value'))
beforeEach(() => {
  vi.clearAllMocks()
  usersApi.getUser.mockResolvedValue({ ...TARGET })
})

describe('create form', () => {
  it('an Admin can pick Admin; a Manager cannot', async () => {
    let w = await open('/admin/users/new', 'admin')
    expect(roleValues(w)).toEqual(['admin', 'manager', 'driver', 'trader', 'client'])
    w = await open('/admin/users/new', 'manager')
    expect(roleValues(w)).toEqual(['manager', 'driver', 'trader', 'client'])
  })

  it('creates a user, never sends status or staff flags, and returns to the list', async () => {
    usersApi.createUser.mockResolvedValue({ id: 20 })
    const w = await open('/admin/users/new')
    await w.find('#uf-full_name').setValue('Sara Nabil')
    await w.find('#uf-phone').setValue('0100 999 8877')
    await w.find('#uf-password').setValue('S0me-Strong-Pass!9')
    await w.find('#uf-role').setValue('client')
    await w.find('form').trigger('submit')
    await flushPromises()
    const body = usersApi.createUser.mock.calls[0][0]
    expect(body).toEqual({
      full_name: 'Sara Nabil',
      phone: '0100 999 8877',
      role: 'client',
      password: 'S0me-Strong-Pass!9',
    })
    expect(Object.keys(body)).not.toContain('status')
    expect(Object.keys(body)).not.toContain('is_staff')
    expect(Object.keys(body)).not.toContain('is_superuser')
    expect(router.currentRoute.value.path).toBe('/admin/users')
  })

  it('requires a username for admin and manager, and a password, before any request', async () => {
    const w = await open('/admin/users/new')
    await w.find('#uf-full_name').setValue('Sara Nabil')
    await w.find('#uf-phone').setValue('01099998877')
    await w.find('#uf-role').setValue('manager')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(usersApi.createUser).not.toHaveBeenCalled()
    expect(w.find('#uf-username-error').exists()).toBe(true)
    expect(w.find('#uf-password-error').exists()).toBe(true)
  })

  it('shows a validation error on the field and keeps the typed values', async () => {
    usersApi.createUser.mockRejectedValue(
      new ApiError({
        status: 400,
        errors: { phone: ['A user with this phone number already exists.'] },
      }),
    )
    const w = await open('/admin/users/new')
    await w.find('#uf-full_name').setValue('Sara Nabil')
    await w.find('#uf-phone').setValue('01099998877')
    await w.find('#uf-password').setValue('S0me-Strong-Pass!9')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('#uf-phone-error').text()).toBe('A user with this phone number already exists.')
    expect(w.find('#uf-full_name').element.value).toBe('Sara Nabil')
    expect(w.find('#uf-password').element.value).toBe('S0me-Strong-Pass!9')
    expect(router.currentRoute.value.path).toBe('/admin/users/new')
  })

  it('a forced 403 shows the server message and keeps the form', async () => {
    usersApi.createUser.mockRejectedValue(
      new ApiError({
        status: 403,
        code: 'admin_protected',
        message: 'You cannot manage an administrator account.',
      }),
    )
    const w = await open('/admin/users/new', 'manager')
    await w.find('#uf-full_name').setValue('Sara Nabil')
    await w.find('#uf-phone').setValue('01099998877')
    await w.find('#uf-password').setValue('S0me-Strong-Pass!9')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').text()).toBe(
      'You cannot manage an administrator account.',
    )
    expect(w.find('#uf-full_name').element.value).toBe('Sara Nabil')
  })
})

describe('edit form', () => {
  it('loads the user and shows the rejection reason and last action as text', async () => {
    const w = await open('/admin/users/9')
    expect(usersApi.getUser).toHaveBeenCalledWith('9')
    expect(w.find('#uf-full_name').element.value).toBe('Omar Khaled')
    expect(w.find('[data-test="rejection-reason"]').text()).toBe('Bad photo')
    expect(w.find('[data-test="last-action"]').text()).toContain('Demo Admin')
    expect(w.find('[data-test="last-action"]').text()).toContain('Rejected')
  })

  it('saves only the changed fields and never status; a blank password is left out', async () => {
    usersApi.updateUser.mockResolvedValue({ ...TARGET, full_name: 'Omar K' })
    const w = await open('/admin/users/9')
    await w.find('#uf-full_name').setValue('Omar K')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(usersApi.updateUser).toHaveBeenCalledWith('9', { full_name: 'Omar K' })
    expect(w.find('[data-test="saved"]').exists()).toBe(true)
  })

  it('sends a new password only when one is typed', async () => {
    usersApi.updateUser.mockResolvedValue({ ...TARGET })
    const w = await open('/admin/users/9')
    await w.find('#uf-password').setValue('Nw7#pQr!vB52xY')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(usersApi.updateUser).toHaveBeenCalledWith('9', { password: 'Nw7#pQr!vB52xY' })
  })

  it('shows retry when the load fails', async () => {
    usersApi.getUser.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open('/admin/users/9')
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.find('#uf-full_name').exists()).toBe(true)
  })

  it('a Manager looking at an Admin gets a read-only form: no save, no delete', async () => {
    usersApi.getUser.mockResolvedValue({ ...TARGET, id: 4, role: 'admin', status: 'active' })
    const w = await open('/admin/users/4', 'manager')
    expect(w.find('[data-test="locked"]').exists()).toBe(true)
    expect(w.find('button[type="submit"]').exists()).toBe(false)
    expect(w.find('[data-test="delete"]').exists()).toBe(false)
    expect(w.find('#uf-full_name').attributes('disabled')).toBeDefined()
    await w.find('form').trigger('submit')
    expect(usersApi.updateUser).not.toHaveBeenCalled()
  })

  it('an Admin can edit another Admin', async () => {
    usersApi.getUser.mockResolvedValue({
      ...TARGET,
      id: 4,
      role: 'admin',
      username: 'boss',
      status: 'active',
    })
    const w = await open('/admin/users/4', 'admin')
    expect(w.find('[data-test="locked"]').exists()).toBe(false)
    expect(w.find('[data-test="delete"]').exists()).toBe(true)
  })

  it('hides delete on your own account and locks your own role', async () => {
    usersApi.getUser.mockResolvedValue({
      ...TARGET,
      id: 1,
      role: 'admin',
      username: 'me',
      status: 'active',
    })
    const w = await open('/admin/users/1', 'admin')
    expect(w.find('[data-test="delete"]').exists()).toBe(false)
    expect(w.find('#uf-role').attributes('disabled')).toBeDefined()
  })
})

describe('delete', () => {
  it('asks first, then deletes and returns to the list', async () => {
    usersApi.deleteUser.mockResolvedValue()
    const w = await open('/admin/users/9')
    await w.find('[data-test="delete"]').trigger('click')
    expect(usersApi.deleteUser).not.toHaveBeenCalled()
    expect(w.find('[data-test="confirm-delete"]').text()).toContain('Omar Khaled')
    await w.find('[data-test="confirm-yes"]').trigger('click')
    await flushPromises()
    expect(usersApi.deleteUser).toHaveBeenCalledWith('9')
    expect(router.currentRoute.value.path).toBe('/admin/users')
  })

  it('cancel keeps the user', async () => {
    const w = await open('/admin/users/9')
    await w.find('[data-test="delete"]').trigger('click')
    await w.find('[data-test="confirm-no"]').trigger('click')
    expect(w.find('[data-test="confirm-delete"]').exists()).toBe(false)
    expect(usersApi.deleteUser).not.toHaveBeenCalled()
  })

  it('a failed delete shows the server message and stays', async () => {
    usersApi.deleteUser.mockRejectedValue(new ApiError({ status: 403, message: 'No.' }))
    const w = await open('/admin/users/9')
    await w.find('[data-test="delete"]').trigger('click')
    await w.find('[data-test="confirm-yes"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').text()).toBe('No.')
    expect(router.currentRoute.value.path).toBe('/admin/users/9')
  })
})

describe('routes', () => {
  it('new comes before :id and both are admin-area children', () => {
    const admin = routes.find((r) => r.path === '/admin')
    const names = admin.children.map((c) => c.name)
    expect(names.indexOf('user-create')).toBeLessThan(names.indexOf('user-edit'))
    expect(router.resolve('/admin/users/new').name).toBe('user-create')
    expect(router.resolve('/admin/users/12').name).toBe('user-edit')
  })
})
