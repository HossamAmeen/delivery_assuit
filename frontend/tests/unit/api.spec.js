import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { http, ApiError } from '@/api/http'
import { getHealth } from '@/api/health'
import { i18n } from '@/i18n'
import { useHealthStore } from '@/stores/health'

const original = http.defaults.adapter

function mockAdapter(handler) {
  http.defaults.adapter = async (config) => {
    const result = await handler(config)
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
}

beforeEach(() => setActivePinia(createPinia()))
afterEach(() => {
  http.defaults.adapter = original
  vi.unstubAllEnvs()
})

describe('health api', () => {
  it('returns data on success and sends the token in development', async () => {
    vi.stubEnv('DEV', true)
    vi.stubEnv('VITE_HEALTH_CHECK_TOKEN', 'pw')
    let seen
    mockAdapter((config) => {
      seen = config
      return { status: 200, data: { success: true, message: 'ok', data: { status: 'healthy' } } }
    })
    expect(await getHealth()).toEqual({ status: 'healthy' })
    expect(seen.url).toBe('health/')
    expect(seen.headers['X-Health-Check-Token']).toBe('pw')
  })

  it('never sends the token outside development', async () => {
    vi.stubEnv('DEV', false)
    vi.stubEnv('VITE_HEALTH_CHECK_TOKEN', 'pw')
    let seen
    mockAdapter((config) => {
      seen = config
      return { status: 200, data: { success: true, data: { status: 'healthy' } } }
    })
    await getHealth()
    expect(seen.headers['X-Health-Check-Token']).toBeUndefined()
  })

  it('normalises the error envelope on a wrong password (403)', async () => {
    mockAdapter(() => ({
      status: 403,
      data: { success: false, message: 'Invalid health check password.', errors: {} },
    }))
    const err = await getHealth().catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ status: 403, message: 'Invalid health check password.' })
    expect(err.isNetworkError).toBe(false)
  })

  it('normalises a network error', async () => {
    mockAdapter(() => new Error('Network Error'))
    const err = await getHealth().catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ status: 0, isNetworkError: true })
  })

  it('handles a non-envelope error body', async () => {
    mockAdapter(() => ({ status: 502, data: '<html>Bad gateway</html>' }))
    const err = await getHealth().catch((e) => e)
    expect(err).toMatchObject({ status: 502, message: '', errors: {} })
  })
})

describe('Accept-Language', () => {
  it.each(['en', 'ar'])('sends the current UI language (%s)', async (lang) => {
    i18n.global.locale.value = lang
    let seen
    mockAdapter((config) => {
      seen = config
      return { status: 200, data: { success: true, data: { status: 'healthy' } } }
    })
    await getHealth()
    expect(seen.headers['Accept-Language']).toBe(lang)
    i18n.global.locale.value = 'en'
  })
})

describe('health store', () => {
  it('goes loading -> healthy', async () => {
    mockAdapter(() => ({ status: 200, data: { success: true, data: { status: 'healthy' } } }))
    const store = useHealthStore()
    const p = store.check()
    expect(store.status).toBe('loading')
    await p
    expect(store.status).toBe('healthy')
  })

  it('goes to error with details on failure', async () => {
    mockAdapter(() => new Error('Network Error'))
    const store = useHealthStore()
    await store.check()
    expect(store.status).toBe('error')
    expect(store.error.isNetworkError).toBe(true)
  })
})
