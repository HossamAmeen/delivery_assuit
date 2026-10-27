import { ERROR_CODES } from '@/api/http'

// Message to show for an auth ApiError. The server `message` is shown as returned (already
// localized by the backend); the i18n fallbacks cover empty messages (network, proxies).
export function authErrorMessage(err, t) {
  if (err?.message) return err.message
  if (err?.isNetworkError) return t('auth.errors.network')
  if (err?.code === ERROR_CODES.ACCOUNT_PENDING) return t('auth.errors.pending')
  if (err?.code === ERROR_CODES.ACCOUNT_DEACTIVATED) return t('auth.errors.deactivated')
  if (err?.code === ERROR_CODES.ACCOUNT_REJECTED) return t('auth.errors.rejected')
  if (err?.status === 401) return t('auth.errors.invalid')
  if (err?.status === 429) return t('auth.errors.rateLimited')
  return t('auth.errors.generic')
}
