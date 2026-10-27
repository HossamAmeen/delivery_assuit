// Shared form helpers for the account and admin screens.

// Counts digits in a phone value. Arabic-Indic and Extended Arabic-Indic digits count
// because the server normalises them.
export function digitCount(value) {
  return String(value ?? '')
    .replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x660))
    .replace(/[۰-۹]/g, (d) => String(d.charCodeAt(0) - 0x6f0))
    .replace(/\D/g, '').length
}

// '' when fine, else 'required' | 'invalid'. The server stays the authority.
export function phoneProblem(value) {
  if (!String(value ?? '').trim()) return 'required'
  const n = digitCount(value)
  return n >= 8 && n <= 15 ? '' : 'invalid'
}

export function emailProblem(value) {
  const v = String(value ?? '').trim()
  return v && !/^\S+@\S+\.\S+$/.test(v) ? 'invalid' : ''
}

// Copies the server `errors` of a 400 onto form fields.
// `fields` maps server key -> form key (or is an array of keys that are the same on both sides).
export function serverFieldErrors(err, fields) {
  const map = Array.isArray(fields) ? Object.fromEntries(fields.map((f) => [f, f])) : fields
  const out = {}
  if (err?.status !== 400) return out
  for (const [serverKey, messages] of Object.entries(err.errors ?? {})) {
    const key = map[serverKey]
    if (key && messages?.length) out[key] = [].concat(messages).join(' ')
  }
  return out
}

// The message for a failure that is not a field error. Only a short server message from
// a 4xx is shown as is; a 5xx, a network failure or an empty body gets the friendly text.
export function formMessage(err, t) {
  if (err?.isNetworkError) return t('auth.errors.network')
  if (err?.status === 429) return t('auth.errors.rateLimited')
  if (err?.status >= 400 && err?.status < 500 && err?.message) return err.message
  return t('auth.errors.generic')
}

// Client-side errors are kept as keys, so a message already on screen follows a language switch.
// Server messages stay plain strings (the backend already localised them).
export const clientError = (key) => ({ key })
export const errorText = (error, t) =>
  error && typeof error === 'object' ? t(error.key) : (error ?? '')
