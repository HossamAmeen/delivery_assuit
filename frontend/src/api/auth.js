import http from './http'

// Auth endpoints. All but `me` are public: `skipAuth` keeps the bearer token and the
// 401 refresh/retry logic away from them (a 401 on login means wrong credentials).
const PUBLIC = { skipAuth: true }

export const REGISTER_ROLES = ['driver', 'trader', 'client']

export async function login({ usernameOrPhone, password }) {
  const { data } = await http.post(
    'auth/token/',
    { username_or_phone: usernameOrPhone, password },
    PUBLIC,
  )
  return data.data // { access, user } — refresh is an HttpOnly cookie
}

export async function register(role, { full_name, phone, password, email }) {
  if (!REGISTER_ROLES.includes(role)) throw new Error(`Unknown registration role: ${role}`)
  const body = { full_name, phone, password }
  if (email) body.email = email
  const { data } = await http.post(`auth/register/${role}/`, body, PUBLIC)
  return { message: data.message, user: data.data.user }
}

// The refresh cookie is sent by the browser. The body is empty; the response is a new access token.
export async function refresh() {
  const { data } = await http.post('auth/token/refresh/', {}, PUBLIC)
  return data.data // { access }
}

export async function logout() {
  await http.post('auth/logout/', {}, PUBLIC)
}

export async function me() {
  const { data } = await http.get('auth/me/')
  return data.data.user
}
