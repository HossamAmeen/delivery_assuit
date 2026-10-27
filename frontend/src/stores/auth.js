import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import * as accountApi from '@/api/account'
import { configureAuth, ERROR_CODES } from '@/api/http'

// The access token lives in memory only. The refresh token is an HttpOnly cookie
// (VULN-012), so this store never reads or writes it. The key below is the old
// localStorage name; it is deleted so a leftover token cannot sit in the browser.
export const REFRESH_STORAGE_KEY = 'delivery.refresh_token'

export const HOME_ROUTES = {
  driver: '/driver',
  trader: '/trader',
  client: '/client',
  admin: '/admin',
  manager: '/admin',
}

// Non-secret marker (no token) that this browser had a session. The refresh cookie is HttpOnly, so
// without it a failed restore cannot tell "session ended elsewhere" from "never signed in" (BUG-010).
const SESSION_FLAG_KEY = 'delivery.has_session'

function hadSession() {
  try {
    return localStorage.getItem(SESSION_FLAG_KEY) === '1'
  } catch {
    return false
  }
}

function setSessionFlag(on) {
  try {
    if (on) localStorage.setItem(SESSION_FLAG_KEY, '1')
    else localStorage.removeItem(SESSION_FLAG_KEY)
  } catch {
    // storage blocked: the notice is just skipped
  }
}

function dropLegacyRefreshToken() {
  try {
    localStorage.removeItem(REFRESH_STORAGE_KEY)
  } catch {
    /* storage unavailable */
  }
}

// Single in-flight refresh shared by every caller (concurrent 401s, restore).
let inFlightRefresh = null
let restorePromise = null

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: null, // memory only, never persisted
    // 'idle' (not restored yet) | 'restoring' | 'authenticated' | 'anonymous'
    status: 'idle',
    // Why the last session ended: '' | 'expired' | 'deactivated' | 'logout' | 'password_changed'
    endedReason: '',
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user && state.accessToken),
    role: (state) => state.user?.role ?? null,
    homeRoute: (state) => HOME_ROUTES[state.user?.role] ?? '/',
  },
  actions: {
    // Wire the http interceptors. `onSessionEnded(reason)` lets the app navigate to login.
    init({ onSessionEnded, onForbidden } = {}) {
      configureAuth({
        getAccessToken: () => this.accessToken,
        refresh: () => this.refreshSession(),
        onForbidden: () => onForbidden?.(),
        onSessionEnded: (reason) => {
          this.clearSession(reason)
          onSessionEnded?.(reason)
        },
      })
    },

    setTokens({ access }) {
      this.accessToken = access
      dropLegacyRefreshToken()
    },

    clearSession(reason = '') {
      this.user = null
      this.accessToken = null
      this.status = 'anonymous'
      this.endedReason = reason
      setSessionFlag(false)
      dropLegacyRefreshToken()
    },

    // Errors (ApiError) propagate; check `err.code` against ERROR_CODES for 403 account states.
    async login({ usernameOrPhone, password }) {
      const data = await authApi.login({ usernameOrPhone, password })
      this.setTokens(data)
      this.user = data.user
      this.status = 'authenticated'
      this.endedReason = ''
      setSessionFlag(true)
      return data.user
    },

    register(role, payload) {
      return authApi.register(role, payload)
    },

    // Asks the browser to send the refresh cookie. Concurrent calls share one request.
    refreshSession() {
      if (inFlightRefresh) return inFlightRefresh
      inFlightRefresh = authApi
        .refresh()
        .then((data) => {
          this.setTokens(data)
          return data.access
        })
        .finally(() => {
          inFlightRefresh = null
        })
      return inFlightRefresh
    },

    // App start: the cookie is HttpOnly, so the only way to know it exists is to use it.
    async restore() {
      dropLegacyRefreshToken()
      this.status = 'restoring'
      try {
        await this.refreshSession()
        this.user = await authApi.me()
        this.status = 'authenticated'
        setSessionFlag(true)
        return true
      } catch (err) {
        const deactivated = err?.code === ERROR_CODES.ACCOUNT_DEACTIVATED
        const originRejected = err?.code === ERROR_CODES.ORIGIN_REJECTED
        const definitive =
          err?.status === 400 ||
          err?.status === 401 ||
          (err?.status === 403 && (deactivated || originRejected))
        if (definitive) {
          // A live session that later fails still sets "expired" via the http interceptor.
          // Only a browser that had a session sees "expired"; a first visit stays quiet.
          this.clearSession(deactivated ? 'deactivated' : hadSession() ? 'expired' : '')
        } else {
          // Network/server trouble: the cookie stays. A later reload can retry.
          this.accessToken = null
          this.user = null
          this.status = 'anonymous'
        }
        return false
      }
    },

    // Runs restore() once and lets every caller (router guard, app start) await the same result.
    ensureRestored() {
      if (this.status !== 'idle' && !restorePromise) return Promise.resolve(this.isAuthenticated)
      if (!restorePromise) {
        restorePromise = this.restore().finally(() => {
          restorePromise = null
        })
      }
      return restorePromise
    },

    async fetchMe() {
      this.user = await authApi.me()
      return this.user
    },

    // The server revokes every refresh token and clears the cookie; the user signs in again.
    async changePassword({ currentPassword, newPassword }) {
      await accountApi.changePassword({ currentPassword, newPassword })
      this.clearSession('password_changed')
    },

    // Keeps the header name in step with the saved profile.
    async updateProfile(fields) {
      const { message, user } = await accountApi.updateProfile(fields)
      this.user = { ...this.user, ...user }
      return message
    },

    // Always ends the local session, even if the server call fails.
    // The cookie is sent by the browser; this function does not pass a token.
    async logout() {
      this.clearSession('logout')
      try {
        await authApi.logout()
      } catch {
        /* best effort: the local session is already gone */
      }
    },
  },
})
