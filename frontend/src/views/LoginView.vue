<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ERROR_CODES } from '@/api/http'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const identifier = ref('')
const password = ref('')
const showPassword = ref(false)
const submitting = ref(false)
const formError = ref('')
// Field -> message. Client-side keys: identifier, password. Server keys are mapped to the same.
const fieldErrors = ref({})

const SERVER_FIELDS = { username_or_phone: 'identifier', password: 'password' }

// Notice about why the previous session ended (shown once the user lands here).
const endedNotice = computed(() => {
  if (auth.endedReason === 'expired') return t('auth.errors.sessionExpired')
  if (auth.endedReason === 'deactivated') return t('auth.errors.deactivated')
  if (auth.endedReason === 'password_changed' || route.query.changed === '1')
    return t('account.password.changedNotice')
  if (route.query.reset === '1') return t('account.reset.doneNotice')
  return ''
})

// Messages come from i18n (never the server text) so they always follow the UI language.
// 401 stays generic: it must not reveal whether the identifier exists.
function messageFor(err) {
  if (err?.isNetworkError) return t('auth.errors.network')
  if (err?.code === ERROR_CODES.ACCOUNT_PENDING) return t('auth.errors.pending')
  if (err?.code === ERROR_CODES.ACCOUNT_DEACTIVATED) return t('auth.errors.deactivated')
  // The server text carries the admin's reason, so it is shown as returned.
  if (err?.code === ERROR_CODES.ACCOUNT_REJECTED) return err.message || t('auth.errors.rejected')
  if (err?.status === 401) return t('auth.errors.invalid')
  if (err?.status === 429) return t('auth.errors.rateLimited')
  return t('auth.errors.generic')
}

function validate() {
  const errors = {}
  if (!identifier.value.trim()) errors.identifier = t('auth.login.required')
  if (!password.value) errors.password = t('auth.login.passwordRequired')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  if (!validate()) return
  submitting.value = true
  try {
    await auth.login({ usernameOrPhone: identifier.value.trim(), password: password.value })
    await router.push(auth.homeRoute)
  } catch (err) {
    const mapped = {}
    if (err?.status === 400) {
      for (const [key, messages] of Object.entries(err.errors ?? {})) {
        const field = SERVER_FIELDS[key]
        if (field && messages?.length) mapped[field] = [].concat(messages).join(' ')
      }
    }
    fieldErrors.value = mapped
    if (Object.keys(mapped).length === 0) formError.value = messageFor(err)
    password.value = ''
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="auth-page">
    <h1>{{ t('auth.pages.login') }}</h1>
    <p
      v-if="route.query.registered === '1'"
      class="auth-notice"
      role="status"
      data-test="registered"
    >
      {{ t('auth.register.success') }}
    </p>
    <p v-if="endedNotice && !formError" class="auth-notice" role="status">{{ endedNotice }}</p>
    <p v-if="formError" class="auth-error" role="alert" data-test="form-error">{{ formError }}</p>

    <form class="auth-form" novalidate @submit.prevent="submit">
      <div class="field">
        <label for="login-identifier">{{ t('auth.login.identifier') }}</label>
        <input
          id="login-identifier"
          v-model="identifier"
          type="text"
          name="username_or_phone"
          autocomplete="username"
          autocapitalize="none"
          spellcheck="false"
          dir="auto"
          :disabled="submitting"
          :aria-invalid="fieldErrors.identifier ? 'true' : 'false'"
          :aria-describedby="
            fieldErrors.identifier ? 'login-identifier-error' : 'login-identifier-hint'
          "
        />
        <p id="login-identifier-hint" class="hint">{{ t('auth.login.identifierHint') }}</p>
        <p v-if="fieldErrors.identifier" id="login-identifier-error" class="field-error">
          {{ fieldErrors.identifier }}
        </p>
      </div>

      <div class="field">
        <label for="login-password">{{ t('auth.login.password') }}</label>
        <div class="password-row">
          <input
            id="login-password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            name="password"
            autocomplete="current-password"
            dir="ltr"
            :disabled="submitting"
            :aria-invalid="fieldErrors.password ? 'true' : 'false'"
            :aria-describedby="fieldErrors.password ? 'login-password-error' : undefined"
          />
          <button
            type="button"
            class="toggle-password"
            data-test="toggle-password"
            :aria-pressed="showPassword ? 'true' : 'false'"
            @click="showPassword = !showPassword"
          >
            {{ showPassword ? t('auth.login.hide') : t('auth.login.show') }}
          </button>
        </div>
        <p v-if="fieldErrors.password" id="login-password-error" class="field-error">
          {{ fieldErrors.password }}
        </p>
      </div>

      <button type="submit" class="submit" :disabled="submitting" :aria-busy="submitting">
        {{ submitting ? t('auth.login.submitting') : t('auth.login.submit') }}
      </button>
    </form>

    <p class="auth-switch">
      <RouterLink to="/forgot-password" class="touch-link" data-test="forgot-link">{{
        t('account.forgot.link')
      }}</RouterLink>
    </p>

    <p class="auth-switch">
      {{ t('auth.login.noAccount') }}
      <RouterLink to="/register" class="touch-link">{{ t('nav.register') }}</RouterLink>
    </p>
  </section>
</template>

<style scoped>
.auth-page {
  max-inline-size: 28rem;
  margin-inline: auto;
}
.auth-form,
.field {
  display: grid;
  gap: 0.375rem;
}
.auth-form {
  gap: 1rem;
}
label {
  font-weight: 600;
}
input {
  font: inherit;
  inline-size: 100%;
  min-inline-size: 0;
  min-block-size: var(--touch-target);
  padding-inline: 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
  color: inherit;
}
input[aria-invalid='true'] {
  border-color: #b42318;
}
.password-row {
  display: flex;
  gap: 0.5rem;
}
.password-row input {
  flex: 1 1 auto;
}
.toggle-password {
  flex: 0 0 auto;
  padding-inline: 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
  cursor: pointer;
}
.submit {
  border: 0;
  border-radius: 0.25rem;
  background: var(--color-primary);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}
.submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.hint,
.field-error,
.auth-error,
.auth-notice {
  margin: 0;
  font-size: 0.875rem;
}
.hint {
  color: #52606d;
}
.field-error {
  color: #b42318;
}
.auth-error,
.auth-notice {
  padding: 0.75rem;
  margin-block-end: 1rem;
  border-inline-start: 4px solid #b42318;
  background: #fef3f2;
}
.auth-notice {
  border-inline-start-color: var(--color-primary);
  background: #eff4ff;
}
.auth-switch {
  margin-block-start: 1.5rem;
}
</style>
