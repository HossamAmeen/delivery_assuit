import http from './http'

// Trader shop profile and items (Sprint 04 contract). Items have no price field here (BR-17).

export async function getShop() {
  const { data } = await http.get('shop/')
  return data.data.shop
}

export async function updateShop(fields) {
  const { data } = await http.patch('shop/', fields)
  return data.data.shop
}

export async function listItems(params = {}) {
  const { data } = await http.get('shop/items/', { params })
  return data.data
}

export async function createItem(fields) {
  const { data } = await http.post('shop/items/', fields)
  return data.data.item
}

export async function updateItem(id, fields) {
  const { data } = await http.patch(`shop/items/${id}/`, fields)
  return data.data.item
}

export async function deleteItem(id) {
  await http.delete(`shop/items/${id}/`)
}
