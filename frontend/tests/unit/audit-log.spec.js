import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes, authGuard } from '@/router'
import AuditView from '@/views/AuditView.vue'
import { ApiError } from '@/api/http'
import * as staffApi from '@/api/staff'
import { plugins, signIn } from './helpers'

vi.mock('@/api/staff', async (orig) => ({ ...(await orig()), listAudit: vi.fn() }))

const ROWS = [
  {
    id: 2,
    action: 'order.status',
    actor: { id: 1, full_name: 'Admin' },
    target_type: 'order',
    target_id: 12,
    detail: 'available -> assigned',
    created_at: '2026-10-27T12:00:00Z',
  },
  {
    id: 1,
    action: 'account.approved',
    actor: null,
    target_type: 'user',
    target_id: 5,
    detail: '',
    created_at: '2026-10-27T11:00:00Z',
  },
]
const page = (results, extra = {}) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
  ...extra,
})

async function open() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('manager')
  const w = mount(AuditView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  staffApi.listAudit.mockResolvedValue(page(structuredClone(ROWS)))
})

describe('audit log', () => {
  it('shows who, what, which target and the detail', async () => {
    const w = await open()
    const rows = w.findAll('[data-test="row"]')
    expect(rows[0].find('[data-test="actor"]').text()).toBe('Admin')
    expect(rows[0].find('[data-test="action"]').text()).toBe('Order status')
    expect(rows[0].find('[data-test="target"]').text()).toBe('order #12')
    expect(rows[0].find('[data-test="detail"]').text()).toBe('available -> assigned')
    expect(rows[1].find('[data-test="actor"]').text()).toBe('—')
  })

  it('shows an unknown action as it is instead of breaking', async () => {
    staffApi.listAudit.mockResolvedValue(page([{ ...ROWS[0], action: 'something.new' }]))
    const w = await open()
    expect(w.find('[data-test="action"]').text()).toBe('something.new')
  })

  it('filters by action from page 1, and pages', async () => {
    staffApi.listAudit.mockResolvedValue(page(structuredClone(ROWS), { next: 'x' }))
    const w = await open()
    await w.find('[data-test="next"]').trigger('click')
    await flushPromises()
    expect(staffApi.listAudit.mock.calls.at(-1)[0]).toEqual({ action: '', page: 2 })
    await w.find('[data-test="action-filter"]').setValue('order.fee')
    await flushPromises()
    expect(staffApi.listAudit.mock.calls.at(-1)[0]).toEqual({ action: 'order.fee', page: 1 })
  })

  it('offers no way to change the log', async () => {
    const w = await open()
    expect(w.findAll('button').map((b) => b.attributes('data-test'))).not.toContain('delete')
    expect(w.find('input[type="text"], textarea').exists()).toBe(false)
  })

  it('shows empty and error with retry', async () => {
    staffApi.listAudit.mockResolvedValueOnce(page([]))
    expect((await open()).find('[data-test="empty"]').exists()).toBe(true)
    staffApi.listAudit.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open()
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.findAll('[data-test="row"]')).toHaveLength(2)
  })

  it('is a staff-only route', () => {
    const admin = routes.find((r) => r.path === '/admin')
    expect(admin.children.find((c) => c.name === 'audit').component).toBe(AuditView)
    setActivePinia(createPinia())
    signIn('client')
    expect(authGuard({ meta: admin.meta })).not.toBe(true)
  })
})
