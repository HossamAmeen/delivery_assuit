<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import FormField from '@/components/FormField.vue'
import { useAuthStore } from '@/stores/auth'
import { formMessage, serverFieldErrors, clientError, errorText } from '@/utils/forms'

const { t } = useI18n()
const msg = (e) => errorText(e, t)
const router = useRouter()
const auth = useAuthStore()

const current = ref('')
const next = ref('')
const confirm = ref('')
const submitting = ref(false)
const formError = ref('')
const fieldErrors = ref({})

function validate() {
  const errors = {}
  if (!current.value)
    errors.current_password = clientError('account.password.errors.currentRequired')
  if (!next.value) errors.new_password = clientError('account.password.errors.newRequired')
  else if (next.value !== confirm.value)
    errors.confirm = clientError('account.password.errors.mismatch')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  if (!validate()) return
  submitting.value = true
  try {
    await auth.changePassword({ currentPassword: current.value, newPassword: next.value })
    await router.replace({ name: 'login', query: { changed: '1' } })
  } catch (err) {
    fieldErrors.value = serverFieldErrors(err, ['current_password', 'new_password'])
    if (Object.keys(fieldErrors.value).length === 0) formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <h1>{{ t('account.password.title') }}</h1>
    <p v-if="formError" class="form-error" role="alert" data-test="form-error">{{ formError }}</p>
    <form class="app-form" novalidate @submit.prevent="submit">
      <FormField
        id="cp-current"
        v-model="current"
        type="password"
        name="current_password"
        autocomplete="current-password"
        dir="ltr"
        :label="t('account.password.current')"
        :error="msg(fieldErrors.current_password)"
        :disabled="submitting"
        required
      />
      <FormField
        id="cp-new"
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
        id="cp-confirm"
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
        {{ submitting ? t('account.password.submitting') : t('account.password.submit') }}
      </button>
    </form>
  </section>
</template>
