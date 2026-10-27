import http from './http'

// Trader locations (Sprint 04 contract). Lists return { count, next, previous, results }.

export async function listLocations(params = {}) {
  const { data } = await http.get('locations/', { params })
  return data.data
}

export async function createLocation(fields) {
  const { data } = await http.post('locations/', fields)
  return data.data.location
}

export async function updateLocation(id, fields) {
  const { data } = await http.patch(`locations/${id}/`, fields)
  return data.data.location
}

export async function deleteLocation(id) {
  await http.delete(`locations/${id}/`)
}
