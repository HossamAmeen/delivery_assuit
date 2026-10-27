import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { plugins } from './helpers'
import HealthStatus from '@/components/HealthStatus.vue'
import { ApiError } from '@/api/http'
import { i18n } from '@/i18n'

vi.mock('@/api/health', () => ({ getHealth: vi.fn() }))
import { getHealth } from '@/api/health'

const mounted = []

async function render() {
  const wrapper = mount(HealthStatus, { global: { plugins: plugins() } })
  mounted.push(wrapper)
  await flushPromises()
  return wrapper
}

afterEach(() => {
  mounted.splice(0).forEach((w) => w.unmount())
})

beforeEach(() => {
  setActivePinia(createPinia())
  vi.mocked(getHealth).mockReset()
})

describe('HealthStatus', () => {
  it('shows loading first', () => {
    vi.mocked(getHealth).mockReturnValue(new Promise(() => {}))
    const wrapper = mount(HealthStatus, { global: { plugins: plugins() } })
    expect(wrapper.text()).toContain('Checking service')
  })

  it('shows Healthy', async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: 'healthy' })
    expect((await render()).text()).toContain('Healthy')
  })

  it('shows a friendly error when the server is unreachable, and retries', async () => {
    vi.mocked(getHealth).mockRejectedValueOnce(new ApiError({ isNetworkError: true }))
    const wrapper = await render()
    expect(wrapper.find('[role="alert"]').text()).toContain('Cannot reach the server')
    vi.mocked(getHealth).mockResolvedValueOnce({ status: 'healthy' })
    await wrapper.find('button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Healthy')
  })

  it('shows a distinct message for a rejected password', async () => {
    vi.mocked(getHealth).mockRejectedValue(new ApiError({ status: 403, message: '' }))
    expect((await render()).text()).toContain('rejected')
  })

  it('shows the server message as returned, and refetches on language change', async () => {
    vi.mocked(getHealth).mockRejectedValueOnce(
      new ApiError({ status: 403, message: 'Invalid health check password.' }),
    )
    const wrapper = await render()
    expect(wrapper.find('[role="alert"]').text()).toContain('Invalid health check password.')
    vi.mocked(getHealth).mockRejectedValueOnce(
      new ApiError({ status: 403, message: 'كلمة مرور فحص الحالة غير صالحة.' }),
    )
    i18n.global.locale.value = 'ar'
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toContain('كلمة مرور فحص الحالة غير صالحة.')
  })

  it('shows the localized fallback on network failure in Arabic', async () => {
    i18n.global.locale.value = 'ar'
    vi.mocked(getHealth).mockRejectedValue(new ApiError({ isNetworkError: true }))
    const wrapper = mount(HealthStatus, { global: { plugins: [createPinia(), i18n] } })
    mounted.push(wrapper)
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toContain('تعذر الوصول إلى الخادم')
  })
})
