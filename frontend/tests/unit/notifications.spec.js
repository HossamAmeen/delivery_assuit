import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import NotificationsView from '@/views/NotificationsView.vue'
import NotificationBell from '@/components/NotificationBell.vue'
import AppHeader from '@/components/AppHeader.vue'
import { ApiError } from '@/api/http'
import * as notificationsApi from '@/api/notifications'
import en from '@/locales/en.json'
import ar from '@/locales/ar.json'
import { plugins, signIn } from './helpers'

vi.mock('@/api/notifications', () => ({
  getUnreadCount: vi.fn(),
  listNotifications: vi.fn(),
  markRead: vi.fn(),
  markAllRead: vi.fn(),
}))

const ROWS = () => [
  {
    id: 3,
    kind: 'order_delivered',
    order_id: 12,
    reference: 'ORD-000012',
    read: false,
    created_at: '2026-10-27T12:00:00Z',
  },
  {
    id: 2,
    kind: 'order_approved',
    order_id: 12,
    reference: 'ORD-000012',
    read: true,
    created_at: '2026-10-27T11:00:00Z',
  },
  {
    id: 1,
    kind: 'account_waiting_approval',
    order_id: null,
    reference: null,
    read: false,
    created_at: '2026-10-27T10:00:00Z',
  },
]
const page = (results, extra = {}) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
  ...extra,
})

async function openPage(role = 'client') {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn(role)
  const w = mount(NotificationsView, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  notificationsApi.listNotifications.mockResolvedValue(page(ROWS()))
  notificationsApi.getUnreadCount.mockResolvedValue(2)
  notificationsApi.markRead.mockResolvedValue({})
  notificationsApi.markAllRead.mockResolvedValue(2)
})
afterEach(() => vi.useRealTimers())

describe('notifications page', () => {
  it('shows each notification as a sentence, newest first, unread marked', async () => {
    const w = await openPage('client')
    const items = w.findAll('[data-test="item"]')
    expect(items).toHaveLength(3)
    expect(items[0].text()).toContain('Your order ORD-000012 was delivered.')
    expect(items[0].find('[data-test="unread"]').exists()).toBe(true)
    expect(items[1].find('[data-test="unread"]').exists()).toBe(false)
  })

  it('links by role: client, trader, driver and staff', async () => {
    const hrefs = {}
    for (const role of ['client', 'trader', 'driver', 'admin']) {
      const w = await openPage(role)
      hrefs[role] = w.findAll('[data-test="open"]').map((a) => a.attributes('href'))
    }
    expect(hrefs.client[0]).toBe('/client/orders/12')
    expect(hrefs.trader[0]).toBe('/trader/orders/12')
    expect(hrefs.driver[0]).toBe('/driver/orders/12')
    expect(hrefs.admin[0]).toBe('/admin/orders/12')
    expect(hrefs.admin[2]).toBe('/admin/approvals')
  })

  it('opening an unread one marks it read; a read one calls nothing', async () => {
    const w = await openPage()
    await w.findAll('[data-test="open"]')[1].trigger('click')
    expect(notificationsApi.markRead).not.toHaveBeenCalled()
    await w.findAll('[data-test="open"]')[0].trigger('click')
    await flushPromises()
    expect(notificationsApi.markRead).toHaveBeenCalledWith(3)
    expect(w.findAll('[data-test="item"]')[0].find('[data-test="unread"]').exists()).toBe(false)
  })

  it('mark all as read updates every row', async () => {
    const w = await openPage()
    await w.find('[data-test="read-all"]').trigger('click')
    await flushPromises()
    expect(notificationsApi.markAllRead).toHaveBeenCalledTimes(1)
    expect(w.findAll('[data-test="unread"]')).toHaveLength(0)
  })

  it('a failed mark-all shows a friendly error', async () => {
    notificationsApi.markAllRead.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await openPage()
    await w.find('[data-test="read-all"]').trigger('click')
    await flushPromises()
    expect(w.find('[data-test="action-error"]').text()).toMatch(/went wrong/i)
    expect(w.findAll('[data-test="unread"]')).toHaveLength(2)
  })

  it('unread-only asks the server and returns to page 1', async () => {
    const w = await openPage()
    await w.find('[data-test="unread-only"]').setValue(true)
    await flushPromises()
    expect(notificationsApi.listNotifications.mock.calls.at(-1)[0]).toEqual({
      page: 1,
      unread: 'true',
    })
  })

  it('shows empty, error with retry, and pages', async () => {
    notificationsApi.listNotifications.mockResolvedValueOnce(page([]))
    expect((await openPage()).find('[data-test="empty"]').exists()).toBe(true)
    notificationsApi.listNotifications.mockRejectedValueOnce(new ApiError({ isNetworkError: true }))
    const w = await openPage()
    expect(w.find('[data-test="load-error"]').text()).toContain('offline')
    notificationsApi.listNotifications.mockResolvedValue(page(ROWS(), { next: 'x' }))
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    await w.find('[data-test="next"]').trigger('click')
    await flushPromises()
    expect(notificationsApi.listNotifications.mock.calls.at(-1)[0].page).toBe(2)
  })

  it('is a route for every signed-in role', () => {
    const route = routes.find((r) => r.name === 'notifications')
    expect(route.meta?.roles).toBeUndefined()
    expect(route.meta?.public).toBeUndefined()
  })

  it('has a sentence for every kind in both languages', () => {
    const kinds = [
      'order_waiting_review',
      'account_waiting_approval',
      'order_approved',
      'order_rejected',
      'order_assigned',
      'order_picked_up',
      'order_in_delivery',
      'order_delivered',
      'order_cancelled',
    ]
    for (const k of kinds) {
      expect(en.notifications.kinds[k]).toBeTruthy()
      expect(ar.notifications.kinds[k]).toBeTruthy()
    }
  })
})

describe('the bell', () => {
  async function bell(role = 'client') {
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    signIn(role)
    const w = mount(NotificationBell, { global: { plugins: plugins([router], pinia) } })
    await flushPromises()
    return w
  }

  it('shows the unread count and links to the page', async () => {
    const w = await bell()
    expect(w.find('[data-testid="notifications-count"]').text()).toBe('2')
    expect(w.find('a').attributes('href')).toBe('/notifications')
    expect(w.find('a').attributes('aria-label')).toContain('2 unread')
  })

  it('shows no badge at zero, and caps large counts', async () => {
    notificationsApi.getUnreadCount.mockResolvedValue(0)
    expect((await bell()).find('[data-testid="notifications-count"]').exists()).toBe(false)
    notificationsApi.getUnreadCount.mockResolvedValue(150)
    expect((await bell()).find('[data-testid="notifications-count"]').text()).toBe('99+')
  })

  it('a failing count never breaks the header', async () => {
    notificationsApi.getUnreadCount.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await bell()
    expect(w.find('a').exists()).toBe(true)
    expect(w.find('[data-testid="notifications-count"]').exists()).toBe(false)
  })

  it('refreshes the count on an interval', async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval', 'setTimeout', 'clearTimeout'] })
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    signIn('client')
    const w = mount(NotificationBell, { global: { plugins: plugins([router], pinia) } })
    await flushPromises()
    notificationsApi.getUnreadCount.mockResolvedValue(5)
    vi.advanceTimersByTime(30000)
    await flushPromises()
    expect(w.find('[data-testid="notifications-count"]').text()).toBe('5')
    w.unmount()
  })

  it('only signed-in users get the bell in the header', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    const pinia = createPinia()
    setActivePinia(pinia)
    signIn(null)
    expect(
      mount(AppHeader, { global: { plugins: plugins([router], pinia) } })
        .find('[data-testid="notifications-link"]')
        .exists(),
    ).toBe(false)
    signIn('client')
    expect(
      mount(AppHeader, { global: { plugins: plugins([router], pinia) } })
        .find('[data-testid="notifications-link"]')
        .exists(),
    ).toBe(true)
  })
})
