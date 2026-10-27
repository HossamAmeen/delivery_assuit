import { createPinia } from 'pinia'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

// Plugins every component test needs. Locale is reset to English for isolation.
// Pass an existing pinia to share state with a store you prepared (see signIn).
export function plugins(extra = [], pinia = createPinia()) {
  i18n.global.locale.value = 'en'
  return [pinia, i18n, ...extra]
}

// Puts the active pinia's auth store into a signed-in (or anonymous) state without any API call.
export function signIn(role) {
  const auth = useAuthStore()
  if (role) {
    auth.user = { id: 1, full_name: 'Test User', role, status: 'active' }
    auth.accessToken = 'access-token'
    auth.status = 'authenticated'
  } else {
    auth.status = 'anonymous'
  }
  return auth
}
