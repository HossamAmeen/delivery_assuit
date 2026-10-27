import { vi } from 'vitest'

// The header bell polls for the unread count on every signed-in screen. Specs that do not
// care about notifications must not hit the network, so it answers 0 by default. A spec that
// tests notifications mocks '@/api/notifications' itself, which takes precedence.
vi.mock('@/api/notifications', () => ({
  getUnreadCount: vi.fn().mockResolvedValue(0),
  listNotifications: vi
    .fn()
    .mockResolvedValue({ count: 0, next: null, previous: null, results: [] }),
  markRead: vi.fn(),
  markAllRead: vi.fn(),
}))
