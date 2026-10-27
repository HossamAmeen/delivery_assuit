import http from './http'

// Staff user management (Admin and Manager). Shapes follow the Sprint 03 contract.

// params: { page, role, status, search }. Empty values are left out of the query.
export async function listUsers(params = {}) {
  const query = {}
  for (const [key, value] of Object.entries(params)) {
    if (value !== '' && value !== null && value !== undefined) query[key] = value
  }
  const { data } = await http.get('users/', { params: query })
  return data.data // { count, next, previous, results }
}

export async function getUser(id) {
  const { data } = await http.get(`users/${id}/`)
  return data.data.user
}

export async function createUser(fields) {
  const { data } = await http.post('users/', fields)
  return data.data.user
}

export async function updateUser(id, fields) {
  const { data } = await http.patch(`users/${id}/`, fields)
  return data.data.user
}

export async function deleteUser(id) {
  await http.delete(`users/${id}/`)
}

export async function approveUser(id) {
  const { data } = await http.post(`users/${id}/approve/`, {})
  return data.data.user
}

export async function rejectUser(id, reason = '') {
  const { data } = await http.post(`users/${id}/reject/`, { reason })
  return data.data.user
}

export async function activateUser(id) {
  const { data } = await http.post(`users/${id}/activate/`, {})
  return data.data.user
}

export async function deactivateUser(id) {
  const { data } = await http.post(`users/${id}/deactivate/`, {})
  return data.data.user
}
