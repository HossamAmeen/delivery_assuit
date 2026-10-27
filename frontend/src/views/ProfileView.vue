<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import FormField from '@/components/FormField.vue'
import ListStatus from '@/components/ListStatus.vue'
import { useAuthStore } from '@/stores/auth'
import {
  emailProblem,
  formMessage,
  phoneProblem,
  serverFieldErrors,
  clientError,
  errorText,
} from '@/utils/forms'

const { t } = useI18n()
const msg = (e) => errorText(e, t)
const auth = useAuthStore()

const profile = ref(null) // the loaded server copy (read-only fields come from here)
const fullName = ref('')
const phone = ref('')
const email = ref('')
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const submitting = ref(false)
const formError = ref('')
const saved = ref(false)
const fieldErrors = ref({})

function fill(user) {
  profile.value = user
  fullName.value = user.full_name ?? ''
  phone.value = user.phone ?? ''
  email.value = user.email ?? ''
}

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    fill(await auth.fetchMe())
  } catch (err) {
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    loading.value = false
  }
}
onMounted(load)

function validate() {
  const errors = {}
  const name = fullName.value.trim()
  if (!name) errors.full_name = clientError('auth.register.errors.nameRequired')
  else if (name.length < 2) errors.full_name = clientError('auth.register.errors.nameShort')
  const p = phoneProblem(phone.value)
  if (p === 'required') errors.phone = clientError('auth.register.errors.phoneRequired')
  else if (p) errors.phone = clientError('auth.register.errors.phoneInvalid')
  if (emailProblem(email.value)) errors.email = clientError('auth.register.errors.emailInvalid')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  saved.value = false
  if (!validate()) return
  submitting.value = true
  try {
    await auth.updateProfile({
      full_name: fullName.value.trim(),
      phone: phone.value.trim(),
      email: email.value.trim(),
    })
    fill(auth.user)
    saved.value = true
  } catch (err) {
    fieldErrors.value = serverFieldErrors(err, ['full_name', 'phone', 'email'])
    if (Object.keys(fieldErrors.value).length === 0) formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <h1>{{ t('account.profile.title') }}</h1>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />

    <template v-if="!loading && !loadError">
      <p v-if="saved" class="form-notice" role="status" data-test="saved">
        {{ t('account.profile.saved') }}
      </p>
      <p v-if="formError" class="form-error" role="alert" data-test="form-error">
        {{ formError }}
      </p>

      <dl class="readonly">
        <div>
          <dt>{{ t('account.profile.username') }}</dt>
          <dd data-test="username">{{ profile.username || t('common.none') }}</dd>
        </div>
        <div>
          <dt>{{ t('userMenu.role') }}</dt>
          <dd data-test="role">{{ t(`roles.${profile.role}`) }}</dd>
        </div>
        <div>
          <dt>{{ t('account.profile.status') }}</dt>
          <dd data-test="status">{{ t(`statuses.${profile.status}`) }}</dd>
        </div>
      </dl>

      <form class="app-form" novalidate @submit.prevent="submit">
        <FormField
          id="pf-full_name"
          v-model="fullName"
          name="full_name"
          autocomplete="name"
          :label="t('account.profile.name')"
          :error="msg(fieldErrors.full_name)"
          :disabled="submitting"
          required
        />
        <FormField
          id="pf-phone"
          v-model="phone"
          type="tel"
          name="phone"
          autocomplete="tel"
          inputmode="tel"
          dir="ltr"
          :label="t('auth.register.phone')"
          :hint="t('auth.register.phoneHint')"
          :error="msg(fieldErrors.phone)"
          :disabled="submitting"
          required
        />
        <FormField
          id="pf-email"
          v-model="email"
          type="email"
          name="email"
          autocomplete="email"
          dir="ltr"
          :label="t('account.profile.email')"
          :error="msg(fieldErrors.email)"
          :disabled="submitting"
        />
        <button
          type="submit"
          class="btn btn-primary"
          :disabled="submitting"
          :aria-busy="submitting"
        >
          {{ submitting ? t('account.profile.saving') : t('account.profile.save') }}
        </button>
      </form>
    </template>
  </section>
</template>

<style scoped>
.readonly {
  display: grid;
  gap: 0.5rem;
  margin: 0 0 1.5rem;
}
.readonly div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}
dt {
  font-weight: 600;
}
dd {
  margin: 0;
  overflow-wrap: anywhere;
}
</style>
