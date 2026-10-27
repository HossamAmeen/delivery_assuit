import axios from 'axios'
import { i18n } from '@/i18n'

// Normalised error thrown by every API call: { status, message, errors, code, isNetworkError }.
// `code` is the optional machine-readable error code (e.g. account_pending, account_deactivated).
// `message` is the server envelope text, already localized by the backend (empty when there is
// none, e.g. network failure: the UI then shows its own localized fallback); clients must key logic on `status`, not on text.
export class ApiError extends Error {
  constructor({ status = 0, message = '', errors = {}, code = '', isNetworkError = false } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.errors = errors
    this.code = code
    this.isNetworkError = isNetworkError
  }
}

export const ERROR_CODES = {
  ACCOUNT_PENDING: 'account_pending',
  ACCOUNT_DEACTIVATED: 'account_deactivated',
  ACCOUNT_REJECTED: 'account_rejected',
  ADMIN_PROTECTED: 'admin_protected',
  ORIGIN_REJECTED: 'origin_rejected',
}

export function normalizeError(error) {
  if (error instanceof ApiError) return error
  const response = error?.response
  if (!response) {
    return new ApiError({ message: '', isNetworkError: true })
  }
  const body = response.data
  const isEnvelope = body && typeof body === 'object' && body.success === false
  return new ApiError({
    status: response.status,
    message: isEnvelope && body.message ? body.message : '',
    errors: isEnvelope && body.errors && typeof body.errors === 'object' ? body.errors : {},
    code: isEnvelope && typeof body.code === 'string' ? body.code : '',
  })
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
  // Sends and stores the HttpOnly refresh cookie. The access token stays a header.
  withCredentials: true,
})

// Auth hooks are injected by the auth store (keeps this module free of store imports).
//   getAccessToken(): string | null       current in-memory access token
//   refresh(): Promise<string>            deduplicated refresh, resolves to the new access token
//   onForbidden(): void                   a 403 that is not an account state
//   onSessionEnded(reason): void          reason: 'expired' | 'deactivated'
let authHandlers = null
export function configureAuth(handlers) {
  authHandlers = handlers
}

// Sends the UI language so server messages come back localized, and attaches the access token.
// Requests with `skipAuth: true` (login, register, refresh, logout) get no token and no refresh handling.
http.interceptors.request.use((config) => {
  config.headers['Accept-Language'] = i18n.global.locale.value
  const token = !config.skipAuth && authHandlers?.getAccessToken?.()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const normalized = normalizeError(error)
    const config = error?.config
    if (!authHandlers || !config || config.skipAuth) throw normalized

    if (normalized.status === 401 && !config._retried) {
      config._retried = true
      let refreshed = false
      try {
        await authHandlers.refresh()
        refreshed = true
      } catch {
        authHandlers.onSessionEnded?.('expired')
      }
      if (refreshed) return http.request(config)
    } else if (normalized.status === 403 && normalized.code === ERROR_CODES.ACCOUNT_DEACTIVATED) {
      authHandlers.onSessionEnded?.('deactivated')
    } else if (normalized.status === 403) {
      // Role/permission refusal: the app sends the user back to their own area.
      authHandlers.onForbidden?.()
    } else if (normalized.status === 401) {
      // Retried request still unauthorized: the session is not usable.
      authHandlers.onSessionEnded?.('expired')
    }
    throw normalized
  },
)

export default http
