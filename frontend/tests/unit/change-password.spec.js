import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import ChangePasswordView from '@/views/ChangePasswordView.vue'
import AppHeader from '@/components/AppHeader.vue'
import { ApiError } from '@/api/http'
import * as accountApi from '@/api/account'
import { useAuthStore } from '@/stores/auth'
import { plugins, signIn } from './helpers'

vi.mock('@/api/account', async (orig) => ({ ...(await orig()), changePassword: vi.fn() }))

let router
let auth
async function open(role = 'client') {
  router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  auth = signIn(role)
  router.push('/account/password')
  await router.isReady()
  return mount(ChangePasswordView, { global: { plugins: plugins([router], pinia) } })
}
async function fill(w, cur = 'old-pass', next = 'New-pass-77!', conf = next) {
  await w.find('#cp-current').setValue(cur)
  await w.find('#cp-new').setValue(next)
  await w.find('#cp-confirm').setValue(conf)
}
async function submit(w) {
  await w.find('form').trigger('submit')
  await flushPromises()
}

beforeEach(() => vi.clearAllMocks())

describe('change password screen', () => {
  it('has labelled fields with the right autocomplete tokens', async () => {
    const w = await open()
    expect(w.find('#cp-current').attributes('autocomplete')).toBe('current-password')
    expect(w.find('#cp-new').attributes('autocomplete')).toBe('new-password')
    expect(w.find('#cp-confirm').attributes('autocomplete')).toBe('new-password')
    expect(w.find('label[for="cp-current"]').text()).toContain('Current password')
    expect(w.find('button[type="submit"]').exists()).toBe(true)
  })

  it('is reachable by every role through the guard', async () => {
    for (const role of ['driver', 'trader', 'client', 'admin', 'manager']) {
      await open(role)
      expect(router.currentRoute.value.name).toBe('change-password')
    }
  })

  it('shows a mismatch without calling the API', async () => {
    const w = await open()
    await fill(w, 'old-pass', 'New-pass-77!', 'different')
    await submit(w)
    expect(accountApi.changePassword).not.toHaveBeenCalled()
    expect(w.find('#cp-confirm-error').text()).toBe('The new passwords do not match.')
  })

  it('requires every field before any request', async () => {
    const w = await open()
    await submit(w)
    expect(accountApi.changePassword).not.toHaveBeenCalled()
    expect(w.find('#cp-current-error').exists()).toBe(true)
    expect(w.find('#cp-new-error').exists()).toBe(true)
  })

  it('shows server field errors on the right fields', async () => {
    accountApi.changePassword.mockRejectedValue(
      new ApiError({
        status: 400,
        errors: {
          current_password: ['Current password is incorrect.'],
          new_password: ['This password is too short.'],
        },
      }),
    )
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('#cp-current-error').text()).toBe('Current password is incorrect.')
    expect(w.find('#cp-new-error').text()).toBe('This password is too short.')
    expect(router.currentRoute.value.name).toBe('change-password')
    expect(auth.isAuthenticated).toBe(true)
  })

  it('on success drops the session and lands on login with a notice', async () => {
    accountApi.changePassword.mockResolvedValue('Password changed. Please log in again.')
    const w = await open()
    await fill(w)
    await submit(w)
    expect(accountApi.changePassword).toHaveBeenCalledWith({
      currentPassword: 'old-pass',
      newPassword: 'New-pass-77!',
    })
    expect(auth.accessToken).toBeNull()
    expect(auth.user).toBeNull()
    expect(auth.endedReason).toBe('password_changed')
    expect(router.currentRoute.value.name).toBe('login')
  })

  it('shows the generic message for a 500 and keeps the session', async () => {
    accountApi.changePassword.mockRejectedValue(
      new ApiError({ status: 500, message: 'An unexpected error occurred.' }),
    )
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('[data-test="form-error"]').text()).toBe(
      'Something went wrong. Please try again.',
    )
    expect(auth.isAuthenticated).toBe(true)
  })
})

describe('auth store changePassword', () => {
  it('calls the API then clears the in-memory session', async () => {
    setActivePinia(createPinia())
    const store = useAuthStore()
    store.user = { id: 1 }
    store.accessToken = 'tok'
    accountApi.changePassword.mockResolvedValue('ok')
    await store.changePassword({ currentPassword: 'a', newPassword: 'b' })
    expect(accountApi.changePassword).toHaveBeenCalledWith({
      currentPassword: 'a',
      newPassword: 'b',
    })
    expect(store.accessToken).toBeNull()
    expect(store.status).toBe('anonymous')
  })

  it('keeps the session when the call fails', async () => {
    setActivePinia(createPinia())
    const store = useAuthStore()
    store.user = { id: 1 }
    store.accessToken = 'tok'
    accountApi.changePassword.mockRejectedValue(new ApiError({ status: 400 }))
    await expect(
      store.changePassword({ currentPassword: 'a', newPassword: 'b' }),
    ).rejects.toBeTruthy()
    expect(store.accessToken).toBe('tok')
  })
})

describe('user menu', () => {
  it('links to change password', async () => {
    router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    signIn('driver')
    const w = mount(AppHeader, { global: { plugins: plugins([router], pinia) } })
    await w.find('[data-testid="user-menu-button"]').trigger('click')
    const link = w.find('[data-testid="menu-password"]')
    expect(link.attributes('href')).toBe('/account/password')
  })
})
