<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import FormField from '@/components/FormField.vue'
import * as accountApi from '@/api/account'
import { formMessage, serverFieldErrors, clientError, errorText } from '@/utils/forms'

const { t } = useI18n()
const msg = (e) => errorText(e, t)
const route = useRoute()
const router = useRouter()

// The token lives only in the address bar and in this request: never in storage.
const token = computed(() => {
  const value = route.query.token
  return typeof value === 'string' ? value : ''
})

const next = ref('')
const confirm = ref('')
const submitting = ref(false)
const formError = ref('')
const fieldErrors = ref({})

function validate() {
  const errors = {}
  if (!next.value) errors.new_password = clientError('account.password.errors.newRequired')
  else if (next.value !== confirm.value)
    errors.confirm = clientError('account.password.errors.mismatch')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  if (!token.value) {
    formError.value = t('account.reset.missingToken')
    return
  }
  if (!validate()) return
  submitting.value = true
  try {
    await accountApi.confirmPasswordReset({ token: token.value, newPassword: next.value })
    await router.replace({ name: 'login', query: { reset: '1' } })
  } catch (err) {
    const mapped = serverFieldErrors(err, { new_password: 'new_password', token: 'token' })
    fieldErrors.value = { new_password: mapped.new_password }
    // An unknown, expired or used link is one message from the server; show it as the form error.
    formError.value = mapped.token ?? (mapped.new_password ? '' : formMessage(err, t))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <h1>{{ t('account.reset.title') }}</h1>
    <p v-if="!token" class="form-error" role="alert" data-test="missing-token">
      {{ t('account.reset.missingToken') }}
    </p>
    <p v-if="formError && token" class="form-error" role="alert" data-test="form-error">
      {{ formError }}
    </p>

    <form class="app-form" novalidate @submit.prevent="submit">
      <FormField
        id="rp-new"
        v-model="next"
        type="password"
        name="new_password"
        autocomplete="new-password"
        dir="ltr"
        :label="t('account.password.new')"
        :hint="t('auth.register.passwordRules')"
        :error="msg(fieldErrors.new_password)"
        :disabled="submitting"
        required
      />
      <FormField
        id="rp-confirm"
        v-model="confirm"
        type="password"
        name="confirm_password"
        autocomplete="new-password"
        dir="ltr"
        :label="t('account.password.confirm')"
        :error="msg(fieldErrors.confirm)"
        :disabled="submitting"
        required
      />
      <button type="submit" class="btn btn-primary" :disabled="submitting" :aria-busy="submitting">
        {{ submitting ? t('account.reset.submitting') : t('account.reset.submit') }}
      </button>
    </form>
    <p>
      <RouterLink to="/forgot-password" class="touch-link">{{
        t('account.reset.askAgain')
      }}</RouterLink>
    </p>
  </section>
</template>
