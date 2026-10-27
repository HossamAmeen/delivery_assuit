import http from './http'

// In-app notifications (Sprint 10 contract). The text is built from `kind` on the screen.

export async function listNotifications(params = {}) {
  const query = {}
  for (const [k, v] of Object.entries(params))
    if (v !== '' && v !== null && v !== undefined) query[k] = v
  const { data } = await http.get('notifications/', { params: query })
  return data.data // { count, next, previous, results }
}

export async function getUnreadCount() {
  const { data } = await http.get('notifications/unread-count/')
  return data.data.count
}

export async function markRead(id) {
  const { data } = await http.post(`notifications/${id}/read/`)
  return data.data.notification
}

export async function markAllRead() {
  const { data } = await http.post('notifications/read-all/')
  return data.data.marked
}
