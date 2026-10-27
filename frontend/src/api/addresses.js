import http from './http'

// Client saved addresses (Sprint 04 contract).

export async function listAddresses(params = {}) {
  const { data } = await http.get('addresses/', { params })
  return data.data
}

export async function createAddress(fields) {
  const { data } = await http.post('addresses/', fields)
  return data.data.address
}

export async function updateAddress(id, fields) {
  const { data } = await http.patch(`addresses/${id}/`, fields)
  return data.data.address
}

export async function deleteAddress(id) {
  await http.delete(`addresses/${id}/`)
}
