import http from './http'

// Self-service account endpoints (Sprint 03 contract).
const PUBLIC = { skipAuth: true }

export async function changePassword({ currentPassword, newPassword }) {
  const { data } = await http.post('auth/password/change/', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return data.message
}

// Only these three fields are ever sent (role and status are not editable here).
export async function updateProfile({ full_name, phone, email }) {
  const { data } = await http.patch('auth/me/', { full_name, phone, email })
  return { message: data.message, user: data.data.user }
}

export async function requestPasswordReset(identifier) {
  const { data } = await http.post('auth/password/reset/', { identifier }, PUBLIC)
  return data.message
}

export async function confirmPasswordReset({ token, newPassword }) {
  const { data } = await http.post(
    'auth/password/reset/confirm/',
    { token, new_password: newPassword },
    PUBLIC,
  )
  return data.message
}
