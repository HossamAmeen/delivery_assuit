import http from './http'

// Staff management of drivers, traders and clients, and item prices (Sprint 07 contract).
export const KINDS = ['drivers', 'traders', 'clients']

function clean(params) {
  const query = {}
  for (const [key, value] of Object.entries(params)) {
    if (value !== '' && value !== null && value !== undefined) query[key] = value
  }
  return query
}

export async function listStaff(kind, params = {}) {
  const { data } = await http.get(`staff/${kind}/`, { params: clean(params) })
  return data.data // { count, next, previous, results }
}

export async function getStaff(kind, id) {
  const { data } = await http.get(`staff/${kind}/${id}/`)
  return data.data
}

// price: a number, or null to clear it.
export async function setItemPrice(id, price) {
  const { data } = await http.patch(`staff/items/${id}/`, { price })
  return data.data.item
}

// Staff: the audit log, read only. params: { action, actor, page }.
export async function listAudit(params = {}) {
  const { data } = await http.get('staff/audit/', { params: clean(params) })
  return data.data // { count, next, previous, results }
}
