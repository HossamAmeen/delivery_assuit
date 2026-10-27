import http from './http'

const HEALTH_HEADER = 'X-Health-Check-Token'

// SECURITY: a token in the browser is not secret. It is sent in development only and is
// never read in production builds. To be reviewed by Security (see docs/TODO.md).
function healthHeaders() {
  const token = import.meta.env.DEV ? import.meta.env.VITE_HEALTH_CHECK_TOKEN : undefined
  return token ? { [HEALTH_HEADER]: token } : {}
}

export async function getHealth() {
  const { data } = await http.get('health/', { headers: healthHeaders() })
  return data.data
}
