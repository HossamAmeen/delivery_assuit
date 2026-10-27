import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import ForgotPasswordView from '@/views/ForgotPasswordView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import LoginView from '@/views/LoginView.vue'
import { ApiError } from '@/api/http'
import * as accountApi from '@/api/account'
import { plugins, signIn } from './helpers'

vi.mock('@/api/account', async (orig) => ({
  ...(await orig()),
  requestPasswordReset: vi.fn(),
  confirmPasswordReset: vi.fn(),
}))

const SAME = 'If an email is on file for that account, a reset link has been sent.'
let router
async function open(component, path, role) {
  router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  router.push(path)
  await router.isReady()
  return mount(component, { global: { plugins: plugins([router], pinia) } })
}
beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})

describe('login', () => {
  it('links to the request screen', async () => {
    const w = await open(LoginView, '/login')
    expect(w.find('[data-test="forgot-link"]').attributes('href')).toBe('/forgot-password')
  })
})

describe('forgot password', () => {
  it('always shows the contact-an-administrator sentence', async () => {
    const w = await open(ForgotPasswordView, '/forgot-password')
    expect(w.find('[data-test="contact-admin"]').text()).toContain('contact an administrator')
    await w.find('#fp-identifier').setValue('01001234567')
    accountApi.requestPasswordReset.mockResolvedValue(SAME)
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="contact-admin"]').exists()).toBe(true)
  })

  it.each(['01001234567', 'ghost', 'nobody@example.com'])(
    'shows the identical confirmation for %s',
    async (id) => {
      accountApi.requestPasswordReset.mockResolvedValue(SAME)
      const w = await open(ForgotPasswordView, '/forgot-password')
      await w.find('#fp-identifier').setValue(` ${id} `)
      await w.find('form').trigger('submit')
      await flushPromises()
      expect(accountApi.requestPasswordReset).toHaveBeenCalledWith(id)
      expect(w.find('[data-test="confirmation"]').text()).toBe(SAME)
    },
  )

  it('needs an identifier before any request', async () => {
    const w = await open(ForgotPasswordView, '/forgot-password')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.requestPasswordReset).not.toHaveBeenCalled()
    expect(w.find('#fp-identifier-error').exists()).toBe(true)
  })

  it('shows the rate-limit message as a form error, not a field error', async () => {
    accountApi.requestPasswordReset.mockRejectedValue(new ApiError({ status: 429 }))
    const w = await open(ForgotPasswordView, '/forgot-password')
    await w.find('#fp-identifier').setValue('a')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').text()).toBe(
      'Too many requests. Please wait a moment.',
    )
    expect(w.find('#fp-identifier-error').exists()).toBe(false)
    expect(w.find('[data-test="confirmation"]').exists()).toBe(false)
  })
})

describe('reset password', () => {
  it('sends the token from the link with a matching password, then goes to login', async () => {
    accountApi.confirmPasswordReset.mockResolvedValue('Password has been reset. Please log in.')
    const w = await open(ResetPasswordView, '/reset-password?token=abc123')
    await w.find('#rp-new').setValue('New-pass-77!')
    await w.find('#rp-confirm').setValue('New-pass-77!')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.confirmPasswordReset).toHaveBeenCalledWith({
      token: 'abc123',
      newPassword: 'New-pass-77!',
    })
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.reset).toBe('1')
  })

  it('a missing token shows an error and never calls the API', async () => {
    const w = await open(ResetPasswordView, '/reset-password')
    expect(w.find('[data-test="missing-token"]').exists()).toBe(true)
    await w.find('#rp-new').setValue('New-pass-77!')
    await w.find('#rp-confirm').setValue('New-pass-77!')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.confirmPasswordReset).not.toHaveBeenCalled()
  })

  it('a mismatch is shown without a request', async () => {
    const w = await open(ResetPasswordView, '/reset-password?token=t')
    await w.find('#rp-new').setValue('one')
    await w.find('#rp-confirm').setValue('two')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.confirmPasswordReset).not.toHaveBeenCalled()
    expect(w.find('#rp-confirm-error').exists()).toBe(true)
  })

  it('shows the server link error and a weak-password field error', async () => {
    accountApi.confirmPasswordReset.mockRejectedValueOnce(
      new ApiError({
        status: 400,
        errors: { token: ['This reset link is invalid or has expired.'] },
      }),
    )
    const w = await open(ResetPasswordView, '/reset-password?token=t')
    await w.find('#rp-new').setValue('x')
    await w.find('#rp-confirm').setValue('x')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').text()).toBe(
      'This reset link is invalid or has expired.',
    )
    accountApi.confirmPasswordReset.mockRejectedValueOnce(
      new ApiError({ status: 400, errors: { new_password: ['This password is too common.'] } }),
    )
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('#rp-new-error').text()).toBe('This password is too common.')
    expect(router.currentRoute.value.name).toBe('reset-password')
  })

  it('stays reachable with a session and never writes the token to storage', async () => {
    const w = await open(ResetPasswordView, '/reset-password?token=secret-token', 'client')
    expect(router.currentRoute.value.name).toBe('reset-password')
    await w.find('#rp-new').setValue('a')
    await w.find('#rp-confirm').setValue('a')
    accountApi.confirmPasswordReset.mockResolvedValue('ok')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(JSON.stringify({ ...localStorage })).not.toContain('secret-token')
    expect(JSON.stringify({ ...sessionStorage })).not.toContain('secret-token')
  })
})
