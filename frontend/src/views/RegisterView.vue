<script setup>
import { computed, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// One form for the three self-registration roles (driver, trader, client).
const props = defineProps({
  role: {
    type: String,
    required: true,
    validator: (v) => ['driver', 'trader', 'client'].includes(v),
  },
})

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const MIN_PASSWORD = 8
const fullName = ref('')
const phone = ref('')
const email = ref('')
const password = ref('')
const confirm = ref('')
const showPassword = ref(false)
const submitting = ref(false)
const formError = ref('')
const fieldErrors = ref({})
const pending = ref(false)
const pendingHeading = ref(null)

const FIELDS = ['full_name', 'phone', 'email', 'password']
const isPendingRole = computed(() => props.role !== 'client')
const nameKey = computed(() => (props.role === 'trader' ? 'nameTrader' : 'name'))

// Arabic-Indic digits are accepted: the server normalises them.
function digitCount(value) {
  return value.replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x660)).replace(/\D/g, '').length
}

function validate() {
  const errors = {}
  const name = fullName.value.trim()
  if (!name) errors.full_name = t('auth.register.errors.nameRequired')
  else if (name.length < 2) errors.full_name = t('auth.register.errors.nameShort')
  if (!phone.value.trim()) errors.phone = t('auth.register.errors.phoneRequired')
  else if (digitCount(phone.value) < 8 || digitCount(phone.value) > 15)
    errors.phone = t('auth.register.errors.phoneInvalid')
  if (email.value.trim() && !/^\S+@\S+\.\S+$/.test(email.value.trim()))
    errors.email = t('auth.register.errors.emailInvalid')
  if (!password.value) errors.password = t('auth.register.errors.passwordRequired')
  else if (password.value.length < MIN_PASSWORD)
    errors.password = t('auth.register.errors.passwordShort')
  if (!errors.password && password.value !== confirm.value)
    errors.confirm = t('auth.register.errors.confirmMismatch')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

function messageFor(err) {
  if (err?.isNetworkError) return t('auth.errors.network')
  if (err?.status === 429) return t('auth.errors.rateLimited')
  return t('auth.errors.generic')
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  if (!validate()) return
  submitting.value = true
  try {
    await auth.register(props.role, {
      full_name: fullName.value.trim(),
      phone: phone.value.trim(),
      password: password.value,
      email: email.value.trim(),
    })
    if (isPendingRole.value) {
      pending.value = true
      // Move focus to the new heading so keyboard/screen-reader users learn the screen changed.
      await nextTick()
      pendingHeading.value?.focus()
    } else {
      await router.push({ name: 'login', query: { registered: '1' } })
    }
  } catch (err) {
    const mapped = {}
    if (err?.status === 400) {
      // Server messages are localized by the backend (Accept-Language), so they are shown as is.
      for (const field of FIELDS) {
        const messages = err.errors?.[field]
        if (messages?.length) mapped[field] = [].concat(messages).join(' ')
      }
    }
    fieldErrors.value = mapped
    if (Object.keys(mapped).length === 0) formError.value = messageFor(err)
    password.value = ''
    confirm.value = ''
  } finally {
    submitting.value = false
  }
}

function describedBy(field, hint) {
  return (
    [fieldErrors.value[field] ? `reg-${field}-error` : null, hint ? `reg-${field}-hint` : null]
      .filter(Boolean)
      .join(' ') || undefined
  )
}
</script>

<template>
  <section v-if="pending" class="auth-page" data-test="pending">
    <h1 ref="pendingHeading" tabindex="-1" data-test="pending-title">
      {{ t('auth.register.pending.title') }}
    </h1>
    <p role="status">{{ t(`auth.register.pending.intro.${role}`) }}</p>
    <h2>{{ t('auth.register.pending.nextTitle') }}</h2>
    <ol>
      <li>{{ t('auth.register.pending.step1') }}</li>
      <li>{{ t('auth.register.pending.step2') }}</li>
      <li>{{ t('auth.register.pending.step3') }}</li>
    </ol>
    <p>
      <RouterLink to="/login" class="touch-link">{{ t('nav.login') }}</RouterLink>
      ·
      <RouterLink to="/" class="touch-link">{{ t('nav.backHome') }}</RouterLink>
    </p>
  </section>

  <section v-else class="auth-page">
    <h1>{{ t(`auth.register.titles.${role}`) }}</h1>
    <p v-if="formError" class="auth-error" role="alert" data-test="form-error">{{ formError }}</p>

    <form class="auth-form" novalidate @submit.prevent="submit">
      <div class="field">
        <label for="reg-full_name">{{ t(`auth.register.${nameKey}`) }}</label>
        <input
          id="reg-full_name"
          v-model="fullName"
          type="text"
          name="full_name"
          autocomplete="name"
          dir="auto"
          :disabled="submitting"
          :aria-invalid="fieldErrors.full_name ? 'true' : 'false'"
          :aria-describedby="describedBy('full_name')"
        />
        <p v-if="fieldErrors.full_name" id="reg-full_name-error" class="field-error">
          {{ fieldErrors.full_name }}
        </p>
      </div>

      <div class="field">
        <label for="reg-phone">{{ t('auth.register.phone') }}</label>
        <input
          id="reg-phone"
          v-model="phone"
          type="tel"
          name="phone"
          autocomplete="tel"
          inputmode="tel"
          dir="ltr"
          :disabled="submitting"
          :aria-invalid="fieldErrors.phone ? 'true' : 'false'"
          :aria-describedby="describedBy('phone', true)"
        />
        <p id="reg-phone-hint" class="hint">{{ t('auth.register.phoneHint') }}</p>
        <p v-if="fieldErrors.phone" id="reg-phone-error" class="field-error">
          {{ fieldErrors.phone }}
        </p>
      </div>

      <div class="field">
        <label for="reg-email">{{ t('auth.register.email') }}</label>
        <input
          id="reg-email"
          v-model="email"
          type="email"
          name="email"
          autocomplete="email"
          autocapitalize="none"
          dir="ltr"
          :disabled="submitting"
          :aria-invalid="fieldErrors.email ? 'true' : 'false'"
          :aria-describedby="describedBy('email', true)"
        />
        <p id="reg-email-hint" class="hint">{{ t('auth.register.emailHint') }}</p>
        <p v-if="fieldErrors.email" id="reg-email-error" class="field-error">
          {{ fieldErrors.email }}
        </p>
      </div>

      <div class="field">
        <label for="reg-password">{{ t('auth.login.password') }}</label>
        <div class="password-row">
          <input
            id="reg-password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            name="password"
            autocomplete="new-password"
            dir="ltr"
            :disabled="submitting"
            :aria-invalid="fieldErrors.password ? 'true' : 'false'"
            :aria-describedby="describedBy('password', true)"
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
        <p id="reg-password-hint" class="hint">{{ t('auth.register.passwordRules') }}</p>
        <p v-if="fieldErrors.password" id="reg-password-error" class="field-error">
          {{ fieldErrors.password }}
        </p>
      </div>

      <div class="field">
        <label for="reg-confirm">{{ t('auth.register.confirm') }}</label>
        <input
          id="reg-confirm"
          v-model="confirm"
          :type="showPassword ? 'text' : 'password'"
          name="confirm_password"
          autocomplete="new-password"
          dir="ltr"
          :disabled="submitting"
          :aria-invalid="fieldErrors.confirm ? 'true' : 'false'"
          :aria-describedby="describedBy('confirm')"
        />
        <p v-if="fieldErrors.confirm" id="reg-confirm-error" class="field-error">
          {{ fieldErrors.confirm }}
        </p>
      </div>

      <button type="submit" class="submit" :disabled="submitting" :aria-busy="submitting">
        {{ submitting ? t('auth.register.submitting') : t('auth.register.submit') }}
      </button>
    </form>

    <p class="auth-switch">
      {{ t('auth.register.haveAccount') }}
      <RouterLink to="/login" class="touch-link">{{ t('nav.login') }}</RouterLink>
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
  min-block-size: var(--touch-target);
  padding-inline: 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
  cursor: pointer;
}
.submit {
  min-block-size: var(--touch-target);
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
.auth-error {
  margin: 0;
  font-size: 0.875rem;
}
.hint {
  color: #52606d;
}
.field-error {
  color: #b42318;
}
.auth-error {
  padding: 0.75rem;
  margin-block-end: 1rem;
  border-inline-start: 4px solid #b42318;
  background: #fef3f2;
}
.auth-switch {
  margin-block-start: 1.5rem;
}
</style>
