import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import { i18n } from '@/i18n'
import en from '@/locales/en.json'
import ar from '@/locales/ar.json'
import ChangePasswordView from '@/views/ChangePasswordView.vue'
import ProfileView from '@/views/ProfileView.vue'
import UserFormView from '@/views/UserFormView.vue'
import ApprovalsView from '@/views/ApprovalsView.vue'
import ForgotPasswordView from '@/views/ForgotPasswordView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import { ApiError } from '@/api/http'
import * as accountApi from '@/api/account'
import * as authApi from '@/api/auth'
import * as usersApi from '@/api/users'
import {
  digitCount,
  emailProblem,
  formMessage,
  phoneProblem,
  serverFieldErrors,
} from '@/utils/forms'
import { plugins, signIn } from './helpers'

vi.mock('@/api/account', async (orig) => ({
  ...(await orig()),
  changePassword: vi.fn(),
  updateProfile: vi.fn(),
  requestPasswordReset: vi.fn(),
  confirmPasswordReset: vi.fn(),
}))
vi.mock('@/api/auth', async (orig) => ({ ...(await orig()), me: vi.fn() }))
vi.mock('@/api/users', async (orig) => ({
  ...(await orig()),
  listUsers: vi.fn(),
  rejectUser: vi.fn(),
  createUser: vi.fn(),
}))

async function mountView(component, path = '/', role = 'admin', locale = 'en') {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  router.push(path)
  await router.isReady()
  const w = mount(component, { global: { plugins: plugins([router], pinia) } })
  i18n.global.locale.value = locale
  await flushPromises()
  return w
}
beforeEach(() => {
  vi.clearAllMocks()
  authApi.me.mockResolvedValue({
    id: 1,
    full_name: 'Ahmed',
    phone: '01001234567',
    email: '',
    role: 'client',
    status: 'active',
    username: null,
  })
})

describe('shared form helpers', () => {
  it('counts Arabic-Indic digits and ignores spaces, dashes and plus', () => {
    expect(digitCount('٠١٠٠ ١٢٣-٤٥٦٧')).toBe(11)
    expect(digitCount('+20 100-123-4567')).toBe(12)
    expect(digitCount('۰۱۰۰۱۲۳۴۵۶۷')).toBe(11)
  })
  it('phoneProblem: required, invalid, fine', () => {
    expect(phoneProblem('  ')).toBe('required')
    expect(phoneProblem('1234567')).toBe('invalid')
    expect(phoneProblem('1'.repeat(16))).toBe('invalid')
    expect(phoneProblem('٠١٠٠١٢٣٤٥٦٧')).toBe('')
  })
  it('emailProblem allows empty and rejects junk', () => {
    expect(emailProblem('')).toBe('')
    expect(emailProblem('a@b.co')).toBe('')
    expect(emailProblem('nope')).toBe('invalid')
  })
  it('serverFieldErrors only maps a 400 and joins messages', () => {
    const err = new ApiError({ status: 400, errors: { phone: ['a', 'b'], other: ['x'] } })
    expect(serverFieldErrors(err, ['phone'])).toEqual({ phone: 'a b' })
    expect(
      serverFieldErrors(new ApiError({ status: 500, errors: { phone: ['a'] } }), ['phone']),
    ).toEqual({})
    expect(serverFieldErrors(err, { phone: 'tel' })).toEqual({ tel: 'a b' })
  })
  it('formMessage: friendly text for network, 429, 5xx and empty; server text only for a 4xx', () => {
    const t = (k) => k
    expect(formMessage(new ApiError({ isNetworkError: true }), t)).toBe('auth.errors.network')
    expect(formMessage(new ApiError({ status: 429, message: 'x' }), t)).toBe(
      'auth.errors.rateLimited',
    )
    expect(formMessage(new ApiError({ status: 500, message: 'Boom trace' }), t)).toBe(
      'auth.errors.generic',
    )
    expect(formMessage(new ApiError({ status: 502 }), t)).toBe('auth.errors.generic')
    expect(formMessage(new ApiError({ status: 403, message: 'No.' }), t)).toBe('No.')
    expect(formMessage(new ApiError({ status: 404 }), t)).toBe('auth.errors.generic')
  })
})

describe('locale files', () => {
  const keys = (o, p = '') =>
    Object.entries(o).flatMap(([k, v]) =>
      v && typeof v === 'object' ? keys(v, `${p}${k}.`) : [`${p}${k}`],
    )
  it('Arabic and English have exactly the same keys', () => {
    expect(keys(ar).sort()).toEqual(keys(en).sort())
  })
})

describe('required fields block the request, in both languages', () => {
  it('change password (English)', async () => {
    const w = await mountView(ChangePasswordView, '/account/password', 'client')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.changePassword).not.toHaveBeenCalled()
    expect(w.find('#cp-current-error').text()).toBe('Enter your current password.')
    expect(w.find('label[for="cp-current"]').text()).toContain('*')
  })

  it('change password (Arabic follows the UI language)', async () => {
    const w = await mountView(ChangePasswordView, '/account/password', 'client', 'ar')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('#cp-current-error').text()).toBe('أدخل كلمة المرور الحالية.')
    expect(w.find('#cp-new-error').text()).toBe('أدخل كلمة مرور جديدة.')
  })

  it('profile with an empty name', async () => {
    const w = await mountView(ProfileView, '/account/profile', 'client')
    await w.find('#pf-full_name').setValue('')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.updateProfile).not.toHaveBeenCalled()
    expect(w.find('#pf-full_name-error').text()).toBe('Enter your name.')
  })

  it('forgot password and reset password', async () => {
    let w = await mountView(ForgotPasswordView, '/forgot-password', undefined)
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.requestPasswordReset).not.toHaveBeenCalled()
    expect(w.find('#fp-identifier-error').exists()).toBe(true)
    w = await mountView(ResetPasswordView, '/reset-password?token=t', undefined)
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.confirmPasswordReset).not.toHaveBeenCalled()
    expect(w.find('#rp-new-error').exists()).toBe(true)
  })

  it('user create and user edit', async () => {
    let w = await mountView(UserFormView, '/admin/users/new')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(usersApi.createUser).not.toHaveBeenCalled()
    for (const id of ['full_name', 'phone', 'password'])
      expect(w.find(`#uf-${id}-error`).exists()).toBe(true)
    // Arabic text for the same screen
    i18n.global.locale.value = 'ar'
    await flushPromises()
    expect(w.find('#uf-full_name-error').text()).toBe('أدخل اسمك.')
    w = await mountView(UserFormView, '/admin/users/new', 'admin', 'ar')
    await w.find('#uf-phone').setValue('١٢٣')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('#uf-phone-error').text()).toBe('أدخل رقم هاتف صحيحًا (من 8 إلى 15 رقمًا).')
  })

  it('reject reason: a too-long reason from the server shows beside the box', async () => {
    usersApi.listUsers.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 5,
          full_name: 'Omar',
          phone: '0100',
          email: '',
          role: 'driver',
          status: 'pending_approval',
        },
      ],
    })
    usersApi.rejectUser.mockRejectedValue(
      new ApiError({
        status: 400,
        errors: { reason: ['Ensure this field has no more than 500 characters.'] },
      }),
    )
    const w = await mountView(ApprovalsView, '/admin/approvals')
    await w.find('[data-test="reject"]').trigger('click')
    await w.find('[data-test="confirm-reject"]').trigger('click')
    await flushPromises()
    expect(w.find('#reason-5-error').text()).toContain('500 characters')
    expect(w.find('[data-test="action-error"]').exists()).toBe(false)
  })
})

describe('unexpected failures show only the friendly message', () => {
  it.each([
    [
      '500 with a body',
      new ApiError({ status: 500, message: 'Traceback: secret', errors: { detail: 'x' } }),
    ],
    ['502 with no body', new ApiError({ status: 502 })],
  ])('profile save: %s', async (_name, err) => {
    accountApi.updateProfile.mockRejectedValue(err)
    const w = await mountView(ProfileView, '/account/profile', 'client')
    await w.find('form').trigger('submit')
    await flushPromises()
    const text = w.find('[data-test="form-error"]').text()
    expect(text).toBe('Something went wrong. Please try again.')
    expect(text).not.toMatch(/Traceback|\{|\}/)
  })

  it('a network error on the user form is the connection message, and values stay', async () => {
    usersApi.createUser.mockRejectedValue(new ApiError({ isNetworkError: true }))
    const w = await mountView(UserFormView, '/admin/users/new')
    await w.find('#uf-full_name').setValue('Sara Nabil')
    await w.find('#uf-phone').setValue('01099998877')
    await w.find('#uf-password').setValue('S0me-Strong-Pass!9')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('[data-test="form-error"]').text()).toBe(
      'Cannot reach the server. Please try again later.',
    )
    expect(w.find('#uf-full_name').element.value).toBe('Sara Nabil')
  })
})
