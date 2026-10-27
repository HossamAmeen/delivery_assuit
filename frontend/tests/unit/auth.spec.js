import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { http, ApiError, configureAuth } from '@/api/http'
import { useAuthStore, REFRESH_STORAGE_KEY } from '@/stores/auth'
import { authErrorMessage } from '@/utils/authErrors'

const original = http.defaults.adapter
const user = { id: 7, full_name: 'Ahmed Ali', role: 'driver', status: 'active' }
const ok = (data, message = 'ok') => ({ status: 200, data: { success: true, message, data } })
const fail = (status, extra = {}) => ({
  status,
  data: { success: false, message: 'Server says no.', errors: {}, ...extra },
})

// routes: { 'POST auth/token/': (config) => response | Error }; records every call in `calls`.
function mockApi(routes) {
  const calls = []
  http.defaults.adapter = async (config) => {
    const key = `${config.method.toUpperCase()} ${config.url}`
    calls.push({ key, config, body: config.data ? JSON.parse(config.data) : undefined })
    const handler = routes[key]
    if (!handler) throw new Error(`Unexpected request ${key}`)
    const result = await handler(config, calls.filter((c) => c.key === key).length)
    if (result instanceof Error) throw result
    const response = { config, headers: {}, statusText: '', ...result }
    if (response.status >= 400) {
      const err = new Error('Request failed')
      err.config = config
      err.response = response
      throw err
    }
    return response
  }
  return calls
}

let store
let ended
beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  store = useAuthStore()
  ended = vi.fn()
  store.init({ onSessionEnded: ended })
})
afterEach(() => {
  http.defaults.adapter = original
  configureAuth(null)
})

describe('login', () => {
  it('stores the user, keeps the access token in memory, and does not persist a refresh token', async () => {
    localStorage.setItem(REFRESH_STORAGE_KEY, 'legacy')
    const calls = mockApi({
      'POST auth/token/': () => ok({ access: 'A1', user }),
    })
    await store.login({ usernameOrPhone: '0100', password: 'pw' })
    expect(calls[0].body).toEqual({ username_or_phone: '0100', password: 'pw' })
    expect(calls[0].config.headers.Authorization).toBeUndefined()
    expect(store.isAuthenticated).toBe(true)
    expect(store.homeRoute).toBe('/driver')
    expect(store.accessToken).toBe('A1')
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
    expect(JSON.stringify(localStorage)).not.toContain('A1')
  })

  it.each([
    ['account_pending', 'Your account is pending approval.'],
    ['account_deactivated', 'Your account has been deactivated.'],
  ])('exposes 403 %s as a typed error and stores nothing', async (code, message) => {
    mockApi({ 'POST auth/token/': () => fail(403, { code, message }) })
    const err = await store.login({ usernameOrPhone: 'x', password: 'y' }).catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ status: 403, code, message })
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
  })

  it('a 401 on login is wrong credentials: no refresh attempt, session untouched callback', async () => {
    const calls = mockApi({
      'POST auth/token/': () => fail(401, { message: 'Invalid credentials.' }),
    })
    const err = await store.login({ usernameOrPhone: 'x', password: 'y' }).catch((e) => e)
    expect(err.status).toBe(401)
    expect(calls).toHaveLength(1)
    expect(ended).not.toHaveBeenCalled()
  })
})

describe('register', () => {
  it('posts to the role URL and returns the summary without tokens', async () => {
    const calls = mockApi({
      'POST auth/register/trader/': () =>
        ok({ user: { id: 1, role: 'trader', status: 'pending_approval' } }, 'Pending.'),
    })
    const res = await store.register('trader', { full_name: 'Shop', phone: '0100', password: 'pw' })
    expect(calls[0].body).toEqual({ full_name: 'Shop', phone: '0100', password: 'pw' })
    expect(res.user.status).toBe('pending_approval')
    expect(store.isAuthenticated).toBe(false)
  })

  it('surfaces field errors and rejects unknown roles', async () => {
    mockApi({
      'POST auth/register/client/': () => fail(400, { errors: { phone: ['Taken.'] } }),
    })
    const err = await store
      .register('client', { full_name: 'A', phone: '1', password: 'p' })
      .catch((e) => e)
    expect(err.errors.phone).toEqual(['Taken.'])
    await expect(store.register('admin', {})).rejects.toThrow()
  })
})

describe('restore', () => {
  it('asks the cookie endpoint and stays anonymous when it is refused', async () => {
    const calls = mockApi({ 'POST auth/token/refresh/': () => fail(401) })
    expect(await store.restore()).toBe(false)
    expect(calls[0].body).toEqual({})
    expect(store.status).toBe('anonymous')
    expect(store.endedReason).toBe('')
  })

  it('drops a legacy localStorage refresh token and does not send it', async () => {
    localStorage.setItem(REFRESH_STORAGE_KEY, 'R1')
    const calls = mockApi({ 'POST auth/token/refresh/': () => fail(401) })
    await store.restore()
    expect(calls[0].body).toEqual({})
    expect(JSON.stringify(calls[0].body)).not.toContain('R1')
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
  })

  it('refreshes with an empty body and loads the profile', async () => {
    const calls = mockApi({
      'POST auth/token/refresh/': () => ok({ access: 'A2' }),
      'GET auth/me/': () => ok({ user: { ...user, phone: '0100' } }),
    })
    expect(await store.restore()).toBe(true)
    expect(calls[0].body).toEqual({})
    expect(calls[1].config.headers.Authorization).toBe('Bearer A2')
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
    expect(store.isAuthenticated).toBe(true)
    expect(store.user.phone).toBe('0100')
  })

  it('clears the session when the refresh cookie is rejected', async () => {
    localStorage.setItem(REFRESH_STORAGE_KEY, 'old')
    mockApi({ 'POST auth/token/refresh/': () => fail(401) })
    expect(await store.restore()).toBe(false)
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
    expect(store.endedReason).toBe('')
    expect(store.isAuthenticated).toBe(false)
  })

  it('shows "expired" when this browser had a session that ended elsewhere (BUG-010)', async () => {
    mockApi({ 'POST auth/token/': () => ok({ access: 'A1', user }) })
    await store.login({ usernameOrPhone: 'x', password: 'y' })
    expect(localStorage.getItem('delivery.has_session')).toBe('1')
    expect(JSON.stringify(localStorage)).not.toContain('A1')

    setActivePinia(createPinia())
    const reloaded = useAuthStore()
    reloaded.init({ onSessionEnded: vi.fn() })
    mockApi({ 'POST auth/token/refresh/': () => fail(401) })
    expect(await reloaded.restore()).toBe(false)
    expect(reloaded.endedReason).toBe('expired')
    expect(localStorage.getItem('delivery.has_session')).toBeNull()
  })

  it('clears the session marker on logout', async () => {
    mockApi({
      'POST auth/token/': () => ok({ access: 'A1', user }),
      'POST auth/logout/': () => ok({}),
    })
    await store.login({ usernameOrPhone: 'x', password: 'y' })
    await store.logout()
    expect(localStorage.getItem('delivery.has_session')).toBeNull()
  })

  it('does not mark the session expired on a network failure', async () => {
    mockApi({ 'POST auth/token/refresh/': () => new Error('Network Error') })
    expect(await store.restore()).toBe(false)
    expect(store.endedReason).toBe('')
    expect(store.status).toBe('anonymous')
  })

  it('treats origin_rejected as a dead session', async () => {
    mockApi({
      'POST auth/token/refresh/': () => fail(403, { code: 'origin_rejected' }),
    })
    expect(await store.restore()).toBe(false)
    expect(store.endedReason).toBe('')
  })
})

describe('401 handling', () => {
  async function signedIn() {
    mockApi({ 'POST auth/token/': () => ok({ access: 'A1', user }) })
    await store.login({ usernameOrPhone: 'x', password: 'y' })
  }

  it('refreshes once, retries with the new token and rotates the refresh token', async () => {
    await signedIn()
    const calls = mockApi({
      'POST auth/token/refresh/': () => ok({ access: 'A2' }),
      'GET things/': (config) =>
        config.headers.Authorization === 'Bearer A2' ? ok({ n: 1 }) : fail(401),
    })
    const { data } = await http.get('things/')
    expect(data.data).toEqual({ n: 1 })
    expect(calls.map((c) => c.key)).toEqual([
      'GET things/',
      'POST auth/token/refresh/',
      'GET things/',
    ])
    expect(calls[1].body).toEqual({})
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
  })

  it('concurrent 401s trigger a single refresh', async () => {
    await signedIn()
    const calls = mockApi({
      'POST auth/token/refresh/': async () => {
        await new Promise((r) => setTimeout(r, 10))
        return ok({ access: 'A2' })
      },
      'GET a/': (c) => (c.headers.Authorization === 'Bearer A2' ? ok({}) : fail(401)),
      'GET b/': (c) => (c.headers.Authorization === 'Bearer A2' ? ok({}) : fail(401)),
      'GET c/': (c) => (c.headers.Authorization === 'Bearer A2' ? ok({}) : fail(401)),
    })
    await Promise.all([http.get('a/'), http.get('b/'), http.get('c/')])
    expect(calls.filter((c) => c.key === 'POST auth/token/refresh/')).toHaveLength(1)
  })

  it('ends the session when the refresh fails', async () => {
    await signedIn()
    mockApi({
      'POST auth/token/refresh/': () => fail(401, { message: 'Token is invalid or expired.' }),
      'GET things/': () => fail(401),
    })
    const err = await http.get('things/').catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(401)
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
    expect(ended).toHaveBeenCalledWith('expired')
  })

  it('does not loop when the retried request is still 401', async () => {
    await signedIn()
    const calls = mockApi({
      'POST auth/token/refresh/': () => ok({ access: 'A2' }),
      'GET things/': () => fail(401),
    })
    await expect(http.get('things/')).rejects.toMatchObject({ status: 401 })
    expect(calls.filter((c) => c.key === 'POST auth/token/refresh/')).toHaveLength(1)
    expect(ended).toHaveBeenCalledWith('expired')
  })

  it('ends the session on 403 account_deactivated from a protected call', async () => {
    await signedIn()
    mockApi({ 'GET things/': () => fail(403, { code: 'account_deactivated' }) })
    const err = await http.get('things/').catch((e) => e)
    expect(err.code).toBe('account_deactivated')
    expect(store.isAuthenticated).toBe(false)
    expect(ended).toHaveBeenCalledWith('deactivated')
  })
})

describe('logout', () => {
  it('logs out with an empty body and clears the memory session', async () => {
    mockApi({ 'POST auth/token/': () => ok({ access: 'A1', user }) })
    await store.login({ usernameOrPhone: 'x', password: 'y' })
    const calls = mockApi({ 'POST auth/logout/': () => ok({}) })
    await store.logout()
    expect(calls[0].body).toEqual({})
    expect(calls[0].config.headers.Authorization).toBeUndefined()
    expect(store.isAuthenticated).toBe(false)
    expect(store.accessToken).toBeNull()
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
  })

  it('still clears the session if the server call fails', async () => {
    mockApi({ 'POST auth/token/': () => ok({ access: 'A1', user }) })
    await store.login({ usernameOrPhone: 'x', password: 'y' })
    mockApi({ 'POST auth/logout/': () => new Error('Network Error') })
    await store.logout()
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem(REFRESH_STORAGE_KEY)).toBeNull()
  })
})

describe('homeRoute and error messages', () => {
  it.each([
    ['driver', '/driver'],
    ['trader', '/trader'],
    ['client', '/client'],
    ['admin', '/admin'],
    ['manager', '/admin'],
  ])('%s -> %s', (role, path) => {
    store.user = { ...user, role }
    expect(store.homeRoute).toBe(path)
  })

  it('prefers the server message and falls back to i18n keys', () => {
    const t = (k) => k
    expect(authErrorMessage(new ApiError({ status: 403, message: 'Server text' }), t)).toBe(
      'Server text',
    )
    expect(authErrorMessage(new ApiError({ isNetworkError: true }), t)).toBe('auth.errors.network')
    expect(authErrorMessage(new ApiError({ status: 403, code: 'account_pending' }), t)).toBe(
      'auth.errors.pending',
    )
    expect(authErrorMessage(new ApiError({ status: 500 }), t)).toBe('auth.errors.generic')
  })
})
