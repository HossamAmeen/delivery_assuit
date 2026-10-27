import http from './http'

// Shops as a client sees them (Sprint 05 contract). No phone numbers, prices may be null.

export async function listShops(params = {}) {
  const query = {}
  for (const [key, value] of Object.entries(params)) {
    if (value !== '' && value !== null && value !== undefined) query[key] = value
  }
  const { data } = await http.get('shops/', { params: query })
  return data.data // { count, next, previous, results }
}

export async function getShop(id) {
  const { data } = await http.get(`shops/${id}/`)
  return data.data.shop
}
