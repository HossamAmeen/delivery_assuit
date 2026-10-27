<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import FormField from '@/components/FormField.vue'
import * as accountApi from '@/api/account'
import { formMessage, serverFieldErrors, clientError, errorText } from '@/utils/forms'

const { t } = useI18n()
const msg = (e) => errorText(e, t)

const identifier = ref('')
const submitting = ref(false)
const formError = ref('')
const fieldError = ref('')
// The API answers the same way for every identifier; the screen never branches on it.
const confirmation = ref('')

async function submit() {
  if (submitting.value) return
  formError.value = ''
  fieldError.value = ''
  if (!identifier.value.trim()) {
    fieldError.value = clientError('account.forgot.required')
    return
  }
  submitting.value = true
  try {
    confirmation.value = await accountApi.requestPasswordReset(identifier.value.trim())
  } catch (err) {
    fieldError.value = serverFieldErrors(err, ['identifier']).identifier ?? ''
    if (!fieldError.value) formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <h1>{{ t('account.forgot.title') }}</h1>
    <p>{{ t('account.forgot.intro') }}</p>
    <p v-if="confirmation" class="form-notice" role="status" data-test="confirmation">
      {{ confirmation }}
    </p>
    <p v-if="formError" class="form-error" role="alert" data-test="form-error">{{ formError }}</p>

    <form class="app-form" novalidate @submit.prevent="submit">
      <FormField
        id="fp-identifier"
        v-model="identifier"
        name="identifier"
        autocomplete="username"
        :label="t('account.forgot.identifier')"
        :hint="t('account.forgot.identifierHint')"
        :error="msg(fieldError)"
        :disabled="submitting"
        required
      />
      <button type="submit" class="btn btn-primary" :disabled="submitting" :aria-busy="submitting">
        {{ submitting ? t('account.forgot.submitting') : t('account.forgot.submit') }}
      </button>
    </form>

    <p class="contact-admin" data-test="contact-admin">{{ t('account.forgot.noEmail') }}</p>
    <p>
      <RouterLink to="/login" class="touch-link">{{ t('account.forgot.backToLogin') }}</RouterLink>
    </p>
  </section>
</template>

<style scoped>
.contact-admin {
  margin-block-start: 1.5rem;
  font-size: 0.875rem;
  color: #52606d;
}
</style>
