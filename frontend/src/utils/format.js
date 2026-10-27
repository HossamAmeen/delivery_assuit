// Date and time shown to users, in the UI language. Empty for a missing value.
export function formatDateTime(iso, locale = 'en') {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}
