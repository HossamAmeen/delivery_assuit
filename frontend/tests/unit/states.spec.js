import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import ListStatus from '@/components/ListStatus.vue'
import ProfileView from '@/views/ProfileView.vue'
import ApprovalsView from '@/views/ApprovalsView.vue'
import { ApiError } from '@/api/http'
import * as accountApi from '@/api/account'
import * as authApi from '@/api/auth'
import * as usersApi from '@/api/users'
import { plugins, signIn } from './helpers'

vi.mock('@/api/account', async (orig) => ({ ...(await orig()), updateProfile: vi.fn() }))
vi.mock('@/api/auth', async (orig) => ({ ...(await orig()), me: vi.fn() }))
vi.mock('@/api/users', async (orig) => ({ ...(await orig()), listUsers: vi.fn() }))

const ME = { id: 1, full_name: 'Ahmed Ali', phone: '01001234567', email: '', role: 'driver' }
const network = () => new ApiError({ isNetworkError: true })

function mountWith(view, role) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  return mount(view, { global: { plugins: plugins([router], pinia) } })
}

function setNavigatorOnline(value) {
  Object.defineProperty(window.navigator, 'onLine', { value, configurable: true })
}

beforeEach(() => {
  vi.clearAllMocks()
  setNavigatorOnline(true)
  authApi.me.mockResolvedValue(ME)
})
afterEach(() => setNavigatorOnline(true))

describe('ListStatus', () => {
  const mountStatus = (props) => mount(ListStatus, { props, global: { plugins: plugins() } })

  it('shows loading, which is not the empty message', () => {
    const w = mountStatus({ loading: true, empty: true, emptyText: 'Nothing here' })
    expect(w.find('[data-test="loading"]').exists()).toBe(true)
    expect(w.find('[data-test="empty"]').exists()).toBe(false)
  })

  it('shows the empty message only when asked', () => {
    const w = mountStatus({ empty: true, emptyText: 'Nothing here' })
    expect(w.find('[data-test="empty"]').text()).toBe('Nothing here')
  })

  it('shows the offline text for a network failure and emits retry on click', async () => {
    const w = mountStatus({ error: 'raw', offline: true })
    expect(w.text()).toContain('offline')
    await w.find('[data-test="retry"]').trigger('click')
    expect(w.emitted('retry')).toHaveLength(1)
  })

  it('follows the browser offline event and retries once when it comes back', async () => {
    const w = mountStatus({ error: 'Server said no' })
    expect(w.text()).toContain('Server said no')
    window.dispatchEvent(new Event('offline'))
    await flushPromises()
    expect(w.text()).toContain('offline')
    window.dispatchEvent(new Event('online'))
    await flushPromises()
    expect(w.text()).toContain('Server said no')
    expect(w.emitted('retry')).toHaveLength(1)
  })

  it('does not retry on reconnect when nothing failed', async () => {
    const w = mountStatus({})
    window.dispatchEvent(new Event('offline'))
    window.dispatchEvent(new Event('online'))
    await flushPromises()
    expect(w.emitted('retry')).toBeUndefined()
  })
})

describe('network failure on the screens', () => {
  it('profile shows the offline message and retry runs the same request again', async () => {
    authApi.me.mockRejectedValueOnce(network())
    const w = mountWith(ProfileView, 'driver')
    await flushPromises()
    expect(w.find('[data-test="load-error"]').text()).toContain('offline')
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(authApi.me).toHaveBeenCalledTimes(2)
    expect(w.find('#pf-full_name').element.value).toBe('Ahmed Ali')
  })

  it('approvals shows the offline message and retry reloads the queue', async () => {
    usersApi.listUsers.mockRejectedValueOnce(network())
    usersApi.listUsers.mockResolvedValue({ count: 0, next: null, previous: null, results: [] })
    const w = mountWith(ApprovalsView, 'admin')
    await flushPromises()
    expect(w.find('[data-test="load-error"]').text()).toContain('offline')
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(usersApi.listUsers).toHaveBeenCalledTimes(2)
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
  })
})

describe('a session that ends during an edit', () => {
  it('keeps the typed values after a failed save', async () => {
    accountApi.updateProfile.mockRejectedValue(new ApiError({ status: 401 }))
    const w = mountWith(ProfileView, 'driver')
    await flushPromises()
    await w.find('#pf-full_name').setValue('Ahmed Zaki')
    await w.find('form').trigger('submit')
    await flushPromises()
    expect(w.find('#pf-full_name').element.value).toBe('Ahmed Zaki')
  })
})
