import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, installGuards } from '@/router'
import { useAuthStore, REFRESH_STORAGE_KEY } from '@/stores/auth'
import { http, configureAuth } from '@/api/http'
import AppShell from '@/components/AppShell.vue'
import { plugins, signIn } from './helpers'

vi.mock('@/api/health', () => ({ getHealth: vi.fn().mockResolvedValue({ status: 'healthy' }) }))

const ROLES = ['driver', 'trader', 'client', 'admin', 'manager']
const HOME = {
  driver: '/driver',
  trader: '/trader',
  client: '/client',
  admin: '/admin',
  manager: '/admin',
}
const AREAS = {
  '/driver': ['driver'],
  '/trader': ['trader'],
  '/client': ['client'],
  '/admin': ['admin', 'manager'],
}

let pinia
function makeRouter() {
  pinia = createPinia()
  setActivePinia(pinia)
  return installGuards(createRouter({ history: createMemoryHistory(), routes }))
}
async function visit(router, path) {
  await router.push(path)
  await router.isReady()
  return router.currentRoute.value
}

beforeEach(() => localStorage.clear())

describe('guard matrix', () => {
  describe('anonymous', () => {
    it.each(Object.keys(AREAS))('%s is refused and sent to login', async (path) => {
      const router = makeRouter()
      signIn(null)
      expect((await visit(router, path)).name).toBe('login')
    })

    it.each(['/', '/login', '/register', '/does/not/exist'])('%s is public', async (path) => {
      const router = makeRouter()
      signIn(null)
      expect((await visit(router, path)).path).toBe(path)
    })
  })

  describe.each(ROLES)('signed in as %s', (role) => {
    it.each(Object.entries(AREAS))('%s access matches the role', async (path, allowed) => {
      const router = makeRouter()
      signIn(role)
      const route = await visit(router, path)
      expect(route.path).toBe(allowed.includes(role) ? path : HOME[role])
    })

    it.each(['/login', '/register'])('%s redirects to own home', async (path) => {
      const router = makeRouter()
      signIn(role)
      expect((await visit(router, path)).path).toBe(HOME[role])
    })

    it.each(['/', '/not/a/page'])('%s (home / 404) stays reachable', async (path) => {
      const router = makeRouter()
      signIn(role)
      expect((await visit(router, path)).path).toBe(path)
    })
  })

  it('decides from store state, not from a token in storage', async () => {
    const router = makeRouter()
    localStorage.setItem(REFRESH_STORAGE_KEY, 'something')
    useAuthStore().status = 'anonymous' // restore finished, no user
    expect((await visit(router, '/driver')).name).toBe('login')
  })
})

describe('session restore', () => {
  it('waits for the stored session before deciding on a direct URL', async () => {
    const router = makeRouter()
    const auth = useAuthStore()
    localStorage.setItem(REFRESH_STORAGE_KEY, 'R1')
    const restore = vi.spyOn(auth, 'restore').mockImplementation(async () => {
      auth.user = { id: 1, role: 'trader', status: 'active' }
      auth.accessToken = 'A'
      auth.status = 'authenticated'
      return true
    })
    expect((await visit(router, '/trader')).path).toBe('/trader')
    expect(restore).toHaveBeenCalledTimes(1)
  })

  it('sends a failed restore to login', async () => {
    const router = makeRouter()
    const auth = useAuthStore()
    vi.spyOn(auth, 'restore').mockImplementation(async () => {
      auth.status = 'anonymous'
      return false
    })
    expect((await visit(router, '/client')).name).toBe('login')
  })
})

describe('logout', () => {
  it('protected URLs redirect to login afterwards', async () => {
    const router = makeRouter()
    const auth = signIn('driver')
    expect((await visit(router, '/driver')).path).toBe('/driver')
    await auth.logout()
    await visit(router, '/') // the app leaves the page on logout; then the URL is typed again
    expect((await visit(router, '/driver')).name).toBe('login')
    expect((await visit(router, '/admin')).name).toBe('login')
  })

  it('the header menu logout ends the session and opens login', async () => {
    const router = makeRouter()
    const auth = signIn('client')
    vi.spyOn(auth, 'logout').mockImplementation(async () => auth.clearSession('logout'))
    await visit(router, '/client')
    const wrapper = mount(AppShell, { global: { plugins: plugins([router], pinia) } })
    await wrapper.find('[data-testid="user-menu-button"]').trigger('click')
    await wrapper.find('[data-testid="logout"]').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('login')
    expect(wrapper.findAll('.bottom-nav a').map((a) => a.attributes('href'))).toEqual([
      '/login',
      '/register',
    ])
  })
})

describe('API 403 handler', () => {
  const original = http.defaults.adapter
  afterEach(() => {
    http.defaults.adapter = original
    configureAuth(null)
  })

  it('calls onForbidden for a permission 403 but keeps the session', async () => {
    makeRouter()
    const auth = signIn('driver')
    const onForbidden = vi.fn()
    const ended = vi.fn()
    auth.init({ onSessionEnded: ended, onForbidden })
    http.defaults.adapter = async (config) => {
      const err = new Error('forbidden')
      err.config = config
      err.response = {
        config,
        status: 403,
        data: { success: false, message: 'No permission.', errors: {} },
      }
      throw err
    }
    await expect(http.get('orders/')).rejects.toMatchObject({ status: 403 })
    expect(onForbidden).toHaveBeenCalledTimes(1)
    expect(ended).not.toHaveBeenCalled()
    expect(auth.isAuthenticated).toBe(true)
  })
})
