import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { readFileSync } from 'node:fs'
import { routes } from '@/router'
import LoginView from '@/views/LoginView.vue'
import { ApiError } from '@/api/http'
import * as authApi from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { i18n } from '@/i18n'
import { plugins } from './helpers'

vi.mock('@/api/auth', async (orig) => ({ ...(await orig()), login: vi.fn() }))

let router
let auth
async function open() {
  router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  auth = useAuthStore()
  auth.status = 'anonymous'
  router.push('/login')
  await router.isReady()
  return mount(LoginView, { global: { plugins: plugins([router], pinia) } })
}
async function fill(w, id = '01001234567', pw = 'secret123') {
  await w.find('#login-identifier').setValue(id)
  await w.find('#login-password').setValue(pw)
}
async function submit(w) {
  await w.find('form').trigger('submit')
  await flushPromises()
}
const fail = (o) => authApi.login.mockRejectedValue(new ApiError(o))

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})

describe('LoginView', () => {
  it('logs in with a trimmed identifier and goes to the role home', async () => {
    authApi.login.mockResolvedValue({
      access: 'a',
      refresh: 'r',
      user: { id: 1, full_name: 'T', role: 'trader', status: 'active' },
    })
    const w = await open()
    await fill(w, '  ahmed  ')
    await submit(w)
    expect(authApi.login).toHaveBeenCalledWith({ usernameOrPhone: 'ahmed', password: 'secret123' })
    expect(router.currentRoute.value.fullPath).toBe('/trader')
  })

  it.each([
    ['driver', '/driver'],
    ['client', '/client'],
    ['manager', '/admin'],
  ])('sends a %s to %s', async (role, path) => {
    authApi.login.mockResolvedValue({ access: 'a', refresh: 'r', user: { id: 1, role } })
    const w = await open()
    await fill(w)
    await submit(w)
    expect(router.currentRoute.value.fullPath).toBe(path)
  })

  it('validates required fields without calling the API', async () => {
    const w = await open()
    await submit(w)
    expect(authApi.login).not.toHaveBeenCalled()
    expect(w.find('#login-identifier-error').text()).toBe('Enter your phone number or username.')
    expect(w.find('#login-password-error').text()).toBe('Enter your password.')
    expect(w.find('#login-identifier').attributes('aria-invalid')).toBe('true')
  })

  it('shows a generic message for invalid credentials and clears the password', async () => {
    fail({ status: 401, message: 'Invalid credentials.' })
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('[data-test=form-error]').text()).toBe('Invalid credentials.')
    expect(w.find('#login-password').element.value).toBe('')
    expect(router.currentRoute.value.name).toBe('login')
  })

  it('shows a friendly pending-approval message from the code', async () => {
    fail({ status: 403, code: 'account_pending', message: 'server text' })
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('[data-test=form-error]').text()).toBe('Your account is pending approval.')
  })

  it('shows a friendly deactivated message from the code', async () => {
    fail({ status: 403, code: 'account_deactivated' })
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('[data-test=form-error]').text()).toContain('deactivated')
  })

  it('shows a rate-limit message on 429', async () => {
    fail({ status: 429, message: 'throttled' })
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('[data-test=form-error]').text()).toBe('Too many requests. Please wait a moment.')
  })

  it('shows a network message when the server is unreachable', async () => {
    fail({ isNetworkError: true })
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('[data-test=form-error]').text()).toContain('Cannot reach the server')
  })

  it('shows server field errors under the fields', async () => {
    fail({ status: 400, errors: { username_or_phone: ['This field may not be blank.'] } })
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('#login-identifier-error').text()).toBe('This field may not be blank.')
    expect(w.find('[data-test=form-error]').exists()).toBe(false)
  })

  it('disables the form while submitting and ignores double submits', async () => {
    let resolve
    authApi.login.mockReturnValue(new Promise((r) => (resolve = r)))
    const w = await open()
    await fill(w)
    await w.find('form').trigger('submit')
    await w.find('form').trigger('submit')
    expect(authApi.login).toHaveBeenCalledTimes(1)
    expect(w.find('button[type=submit]').attributes('disabled')).toBeDefined()
    expect(w.find('#login-identifier').attributes('disabled')).toBeDefined()
    resolve({ access: 'a', refresh: 'r', user: { id: 1, role: 'client' } })
    await flushPromises()
  })

  it('toggles password visibility', async () => {
    const w = await open()
    expect(w.find('#login-password').attributes('type')).toBe('password')
    await w.find('[data-test=toggle-password]').trigger('click')
    expect(w.find('#login-password').attributes('type')).toBe('text')
  })

  it('has labelled inputs, a register link and an expiry notice', async () => {
    const w = await open()
    expect(w.find('label[for=login-identifier]').exists()).toBe(true)
    expect(w.find('label[for=login-password]').exists()).toBe(true)
    expect(w.find('a[href="/register"]').exists()).toBe(true)
    auth.endedReason = 'expired'
    await flushPromises()
    expect(w.find('[role=status]').text()).toContain('expired')
  })

  it('renders in Arabic', async () => {
    const w = await open()
    i18n.global.locale.value = 'ar'
    await flushPromises()
    expect(w.find('h1').text()).toBe('تسجيل الدخول')
    expect(w.find('label[for=login-identifier]').text()).toBe('رقم الهاتف أو اسم المستخدم')
    fail({ status: 403, code: 'account_pending' })
    await fill(w)
    await submit(w)
    expect(w.find('[data-test=form-error]').text()).toBe('حسابك قيد المراجعة والموافقة.')
    i18n.global.locale.value = 'en'
  })

  it('keeps en and ar login keys in sync and the route meta intact', () => {
    const keys = (l) =>
      Object.keys(JSON.parse(readFileSync(`src/locales/${l}.json`, 'utf8')).auth.login).sort()
    expect(keys('ar')).toEqual(keys('en'))
    const r = routes.find((x) => x.name === 'login')
    expect(r.meta).toEqual({ public: true, guestOnly: true })
    expect(r.component).toBe(LoginView)
  })
})
