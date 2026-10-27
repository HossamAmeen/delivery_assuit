import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import ProfileView from '@/views/ProfileView.vue'
import AppHeader from '@/components/AppHeader.vue'
import { ApiError } from '@/api/http'
import * as accountApi from '@/api/account'
import * as authApi from '@/api/auth'
import { plugins, signIn } from './helpers'

vi.mock('@/api/account', async (orig) => ({ ...(await orig()), updateProfile: vi.fn() }))
vi.mock('@/api/auth', async (orig) => ({ ...(await orig()), me: vi.fn() }))

const ME = {
  id: 1,
  full_name: 'Ahmed Ali',
  phone: '01001234567',
  username: null,
  email: '',
  role: 'driver',
  status: 'active',
  rejection_reason: '',
}
let auth
let pinia
async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  pinia = createPinia()
  setActivePinia(pinia)
  auth = signIn('driver')
  return mount(ProfileView, { global: { plugins: plugins([router], pinia) } })
}
beforeEach(() => {
  vi.clearAllMocks()
  authApi.me.mockResolvedValue(ME)
})

describe('profile screen', () => {
  it('shows a loading state, then the contract fields', async () => {
    const w = await open()
    expect(w.find('[data-test="loading"]').exists()).toBe(true)
    await flushPromises()
    expect(w.find('#pf-full_name').element.value).toBe('Ahmed Ali')
    expect(w.find('#pf-phone').element.value).toBe('01001234567')
    expect(w.find('[data-test="username"]').text()).toBe('—')
    expect(w.find('[data-test="role"]').text()).toBe('Driver')
    expect(w.find('[data-test="status"]').text()).toBe('Active')
  })

  it('offers no input for role, status, or username', async () => {
    const w = await open()
    await flushPromises()
    const names = w.findAll('input').map((i) => i.attributes('name'))
    expect(names.sort()).toEqual(['email', 'full_name', 'phone'])
  })

  it('shows a retryable error when the load fails', async () => {
    authApi.me.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    await flushPromises()
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(authApi.me).toHaveBeenCalledTimes(2)
    expect(w.find('#pf-full_name').exists()).toBe(true)
  })

  it('saves only name, phone and email and updates the header name', async () => {
    accountApi.updateProfile.mockResolvedValue({
      message: 'Profile updated.',
      user: { ...ME, full_name: 'Ahmed Z', phone: '01005556677', email: 'a@x.com' },
    })
    const w = await open()
    await flushPromises()
    await w.find('#pf-full_name').setValue('  Ahmed Z ')
    await w.find('#pf-phone').setValue('0100 555 6677')
    await w.find('#pf-email').setValue('a@x.com')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.updateProfile).toHaveBeenCalledWith({
      full_name: 'Ahmed Z',
      phone: '0100 555 6677',
      email: 'a@x.com',
    })
    expect(auth.user.full_name).toBe('Ahmed Z')
    expect(auth.user.role).toBe('driver')
    expect(w.find('[data-test="saved"]').exists()).toBe(true)
    // the header reads the same store
    const header = mount(AppHeader, {
      global: {
        plugins: plugins([createRouter({ history: createMemoryHistory(), routes })], pinia),
      },
    })
    expect(header.find('.user-menu-name').text()).toBe('Ahmed Z')
  })

  it('lets the user clear the email', async () => {
    accountApi.updateProfile.mockResolvedValue({ message: 'ok', user: ME })
    authApi.me.mockResolvedValue({ ...ME, email: 'old@x.com' })
    const w = await open()
    await flushPromises()
    await w.find('#pf-email').setValue('')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.updateProfile.mock.calls[0][0].email).toBe('')
  })

  it('shows duplicate phone and email messages on their fields', async () => {
    accountApi.updateProfile.mockRejectedValue(
      new ApiError({
        status: 400,
        errors: {
          phone: ['A user with this phone number already exists.'],
          email: ['A user with this email already exists.'],
        },
      }),
    )
    const w = await open()
    await flushPromises()
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('#pf-phone-error').text()).toBe('A user with this phone number already exists.')
    expect(w.find('#pf-email-error').text()).toBe('A user with this email already exists.')
    expect(w.find('#pf-full_name').element.value).toBe('Ahmed Ali')
  })

  it('blocks an invalid phone without a request', async () => {
    const w = await open()
    await flushPromises()
    await w.find('#pf-phone').setValue('123')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(accountApi.updateProfile).not.toHaveBeenCalled()
    expect(w.find('#pf-phone-error').exists()).toBe(true)
  })

  it('only ever loads the signed-in user through /auth/me/', async () => {
    await open()
    await flushPromises()
    expect(authApi.me).toHaveBeenCalledWith()
  })
})

describe('profile route', () => {
  it('is linked from the user menu', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia2 = createPinia()
    setActivePinia(pinia2)
    signIn('client')
    const w = mount(AppHeader, { global: { plugins: plugins([router], pinia2) } })
    await w.find('[data-testid="user-menu-button"]').trigger('click')
    expect(w.find('[data-testid="menu-profile"]').attributes('href')).toBe('/account/profile')
  })
})
