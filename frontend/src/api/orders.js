import http from './http'

// Orders (Sprint 05 contract). Places are copied into the order by the server.

export async function listOrders(params = {}) {
  const query = {}
  for (const [key, value] of Object.entries(params)) {
    if (value !== '' && value !== null && value !== undefined) query[key] = value
  }
  const { data } = await http.get('orders/', { params: query })
  return data.data
}

export async function createOrder(body) {
  const { data } = await http.post('orders/', body)
  return data.data.order
}

export async function approveOrder(id, deliveryFee = null) {
  const body = deliveryFee === null ? {} : { delivery_fee: deliveryFee }
  const { data } = await http.post(`orders/${id}/approve/`, body)
  return data.data.order
}

export async function rejectOrder(id, reason) {
  const { data } = await http.post(`orders/${id}/reject/`, { reason })
  return data.data.order
}

export async function getOrder(id) {
  const { data } = await http.get(`orders/${id}/`)
  return data.data.order
}

// Staff: active drivers and whether each is busy. { count, next, previous, results }
export async function listDrivers(params = {}) {
  const { data } = await http.get('drivers/', { params })
  return data.data
}

export async function assignOrder(id, driverId) {
  const { data } = await http.post(`orders/${id}/assign/`, { driver: driverId })
  return data.data.order
}

// Driver: move the order to its next step. The server decides which one.
export async function advanceOrder(id) {
  const { data } = await http.post(`orders/${id}/advance/`)
  return data.data.order
}

// Staff: set or change the delivery fee (until the order is finished).
export async function setFee(id, deliveryFee) {
  const { data } = await http.patch(`orders/${id}/fee/`, { delivery_fee: deliveryFee })
  return data.data.order
}

// Client (before assignment) or staff (with a reason): cancel an order.
export async function cancelOrder(id, reason = '') {
  const { data } = await http.post(`orders/${id}/cancel/`, reason ? { reason } : {})
  return data.data.order
}

// Counts of the orders the caller may see: total, waiting_review, waiting_for_driver,
// in_progress, delivered, cancelled.
export async function getSummary() {
  const { data } = await http.get('orders/summary/')
  return data.data
}

// Client (or staff) edits an order before a driver is assigned. Same fields as creation.
export async function updateOrder(id, body) {
  const { data } = await http.patch(`orders/${id}/`, body)
  return data.data.order
}

// Client rates the driver of a delivered order, once. score 1 to 5, comment optional.
export async function rateOrder(id, score, comment = '') {
  const { data } = await http.post(`orders/${id}/rating/`, comment ? { score, comment } : { score })
  return data.data.order
}

// Driver: own performance. month is 'YYYY-MM' or empty for all-time.
export async function getMyPerformance(month = '') {
  const { data } = await http.get('drivers/me/performance/', { params: month ? { month } : {} })
  return data.data
}

// Staff: dashboard counts. params: { period, from, to }.
export async function getDashboard(params = {}) {
  const query = {}
  for (const [k, v] of Object.entries(params)) if (v) query[k] = v
  const { data } = await http.get('staff/dashboard/', { params: query })
  return data.data
}

// Staff: every driver's performance. params: { month, ordering, page }.
export async function listDriverPerformance(params = {}) {
  const query = {}
  for (const [k, v] of Object.entries(params)) if (v) query[k] = v
  const { data } = await http.get('staff/drivers/performance/', { params: query })
  return data.data
}
