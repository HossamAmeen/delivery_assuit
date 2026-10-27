import { readFileSync } from 'node:fs'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import RegisterView from '@/views/RegisterView.vue'
import RegisterChooserView from '@/views/RegisterChooserView.vue'
import LoginView from '@/views/LoginView.vue'
import { ApiError } from '@/api/http'
import * as authApi from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { i18n } from '@/i18n'
import { plugins } from './helpers'

vi.mock('@/api/auth', async (orig) => ({ ...(await orig()), register: vi.fn() }))

let router
async function open(role = 'client') {
  router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().status = 'anonymous'
  router.push(`/register/${role}`)
  await router.isReady()
  return mount(RegisterView, { props: { role }, global: { plugins: plugins([router], pinia) } })
}
async function fill(w, o = {}) {
  const v = {
    name: 'Ahmed Ali',
    phone: '0100 123 4567',
    pw: 'S0me-Strong-Pass',
    confirm: undefined,
    ...o,
  }
  await w.find('#reg-full_name').setValue(v.name)
  await w.find('#reg-phone').setValue(v.phone)
  if (v.email) await w.find('#reg-email').setValue(v.email)
  await w.find('#reg-password').setValue(v.pw)
  await w.find('#reg-confirm').setValue(v.confirm ?? v.pw)
}
async function submit(w) {
  await w.find('form').trigger('submit')
  await flushPromises()
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('register routes', () => {
  it('has the chooser and one route per role, guest only', () => {
    for (const name of ['register', 'register-driver', 'register-trader', 'register-client']) {
      const r = routes.find((x) => x.name === name)
      expect(r.meta).toMatchObject({ public: true, guestOnly: true })
    }
  })
  it('chooser links to the three forms', async () => {
    const w = mount(RegisterChooserView, {
      global: { plugins: plugins([createRouter({ history: createMemoryHistory(), routes })]) },
    })
    expect(w.findAll('a.role-card').map((a) => a.attributes('href'))).toEqual([
      '/register/client',
      '/register/driver',
      '/register/trader',
    ])
  })
})

describe('RegisterView', () => {
  it('uses the shop/trader label for traders only', async () => {
    expect((await open('trader')).find('label[for="reg-full_name"]').text()).toBe(
      'Shop or trader name',
    )
    expect((await open('driver')).find('label[for="reg-full_name"]').text()).toBe('Full name')
  })

  it('shows the password rules', async () => {
    const w = await open()
    expect(w.find('#reg-password-hint').text()).toMatch(/8 characters/)
    expect(w.find('#reg-password').attributes('aria-describedby')).toContain('reg-password-hint')
  })

  it('shows required-field errors per field without calling the API', async () => {
    const w = await open()
    await submit(w)
    expect(authApi.register).not.toHaveBeenCalled()
    for (const f of ['full_name', 'phone', 'password']) {
      expect(w.find(`#reg-${f}-error`).exists()).toBe(true)
      expect(w.find(`#reg-${f}`).attributes('aria-invalid')).toBe('true')
    }
  })

  it('validates phone length, email, password length and confirmation', async () => {
    const w = await open()
    await fill(w, { phone: '123', email: 'nope', pw: 'short', confirm: 'short' })
    await submit(w)
    expect(w.find('#reg-phone-error').exists()).toBe(true)
    expect(w.find('#reg-email-error').exists()).toBe(true)
    expect(w.find('#reg-password-error').exists()).toBe(true)
    await fill(w, { pw: 'S0me-Strong-Pass', confirm: 'different-pass' })
    await submit(w)
    expect(w.find('#reg-confirm-error').text()).toMatch(/do not match/)
    expect(authApi.register).not.toHaveBeenCalled()
  })

  it('accepts Arabic-Indic digits in the phone', async () => {
    authApi.register.mockResolvedValue({ message: '', user: {} })
    const w = await open('driver')
    await fill(w, { phone: '٠١٠٠١٢٣٤٥٦٧' })
    await submit(w)
    expect(authApi.register).toHaveBeenCalled()
  })

  it('client success goes to login with a success note', async () => {
    authApi.register.mockResolvedValue({ message: 'ok', user: { role: 'client' } })
    const w = await open('client')
    await fill(w, { email: ' a@b.co ' })
    await submit(w)
    expect(authApi.register).toHaveBeenCalledWith('client', {
      full_name: 'Ahmed Ali',
      phone: '0100 123 4567',
      password: 'S0me-Strong-Pass',
      email: 'a@b.co',
    })
    expect(router.currentRoute.value.name).toBe('login')
    const login = mount(LoginView, { global: { plugins: plugins([router], createPinia()) } })
    expect(login.find('[data-test="registered"]').exists()).toBe(true)
  })

  it.each(['driver', 'trader'])('%s success shows the pending approval screen', async (role) => {
    authApi.register.mockResolvedValue({ message: 'ok', user: { role } })
    const w = await open(role)
    await fill(w)
    await submit(w)
    expect(authApi.register).toHaveBeenCalledWith(role, expect.any(Object))
    expect(w.find('[data-test="pending"]').exists()).toBe(true)
    expect(w.find('form').exists()).toBe(false)
    expect(w.findAll('ol li').length).toBe(3)
    expect(router.currentRoute.value.path).toBe(`/register/${role}`)
  })

  it.each(['driver', 'trader'])(
    '%s pending screen moves focus to its heading (BUG-008)',
    async (role) => {
      authApi.register.mockResolvedValue({ message: 'ok', user: { role } })
      const w = await open(role)
      document.body.appendChild(w.element.parentNode ?? w.element)
      await fill(w)
      await submit(w)
      await flushPromises()
      const h1 = w.find('[data-test="pending-title"]')
      expect(h1.element.tagName).toBe('H1')
      expect(document.activeElement).toBe(h1.element)
      w.unmount()
    },
  )

  it('keeps focused fields clear of the fixed bottom nav via scroll-padding-bottom (BUG-009)', () => {
    const css = readFileSync('src/assets/main.css', 'utf8')
    expect(css).toMatch(/html\s*\{[^}]*scroll-padding-bottom:[^;]*var\(--bottom-nav-height\)/)
  })

  it('shows server field errors per field and clears passwords', async () => {
    authApi.register.mockRejectedValue(
      new ApiError({
        status: 400,
        errors: {
          phone: ['A user with this phone number already exists.'],
          password: ['This password is too common.', 'This password is entirely numeric.'],
          email: ['A user with this email already exists.'],
          full_name: ['This field is required.'],
        },
      }),
    )
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('#reg-phone-error').text()).toContain('already exists')
    expect(w.find('#reg-password-error').text()).toContain('too common')
    expect(w.find('#reg-password-error').text()).toContain('entirely numeric')
    expect(w.find('#reg-email-error').text()).toContain('email already exists')
    expect(w.find('#reg-full_name-error').exists()).toBe(true)
    expect(w.find('[data-test="form-error"]').exists()).toBe(false)
    expect(w.find('#reg-password').element.value).toBe('')
    expect(w.find('#reg-full_name').element.value).toBe('Ahmed Ali')
  })

  it.each([
    [{ isNetworkError: true }, /Cannot reach/],
    [{ status: 429 }, /Too many/],
    [{ status: 500 }, /Something went wrong/],
  ])('maps %o to a localized form error', async (opts, re) => {
    authApi.register.mockRejectedValue(new ApiError(opts))
    const w = await open()
    await fill(w)
    await submit(w)
    expect(w.find('[data-test="form-error"]').text()).toMatch(re)
    expect(w.find('[data-test="form-error"]').attributes('role')).toBe('alert')
  })

  it('renders Arabic texts', async () => {
    const w = await open('trader')
    i18n.global.locale.value = 'ar'
    await flushPromises()
    expect(w.find('label[for="reg-full_name"]').text()).toBe('اسم المتجر أو التاجر')
  })

  it('toggles password visibility for both password fields', async () => {
    const w = await open()
    await w.find('[data-test="toggle-password"]').trigger('click')
    expect(w.find('#reg-password').attributes('type')).toBe('text')
    expect(w.find('#reg-confirm').attributes('type')).toBe('text')
  })
})
