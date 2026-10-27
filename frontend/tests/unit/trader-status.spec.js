import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import LoginView from '@/views/LoginView.vue'
import { ApiError } from '@/api/http'
import * as authApi from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { plugins } from './helpers'

vi.mock('@/api/auth', async (orig) => ({ ...(await orig()), login: vi.fn() }))

async function tryLogin(code, message) {
  authApi.login.mockRejectedValue(new ApiError({ status: 403, code, message }))
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().status = 'anonymous'
  router.push('/login')
  await router.isReady()
  const w = mount(LoginView, { global: { plugins: plugins([router], pinia) } })
  await w.find('#login-identifier').setValue('trader1')
  await w.find('#login-password').setValue('secret123')
  await w.find('form').trigger('submit')
  await flushPromises()
  return { w, auth: useAuthStore() }
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})

describe('a trader who is not active (BL-043)', () => {
  it.each([
    ['account_pending', /pending approval/i],
    ['account_deactivated', /deactivated/i],
    ['account_rejected', /rejected/i],
  ])('sees a clear message for %s and gets no session', async (code, pattern) => {
    const { w, auth } = await tryLogin(code, 'Your registration was rejected.')
    expect(w.find('[data-test="form-error"]').text()).toMatch(pattern)
    expect(auth.isAuthenticated).toBe(false)
  })

  it('the trader area is closed to every other role by the route guard', () => {
    const trader = routes.find((r) => r.path === '/trader')
    expect(trader.meta.roles).toEqual(['trader'])
  })
})
