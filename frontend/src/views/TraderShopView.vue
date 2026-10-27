<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import FormField from '@/components/FormField.vue'
import ListStatus from '@/components/ListStatus.vue'
import * as shopApi from '@/api/shop'
import { clientError, errorText, formMessage, phoneProblem, serverFieldErrors } from '@/utils/forms'

const { t } = useI18n()
const msg = (e) => errorText(e, t)

const shop = ref(null)
const name = ref('')
const phone = ref('')
const description = ref('')
const available = ref(false)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const submitting = ref(false)
const formError = ref('')
const saved = ref(false)
const fieldErrors = ref({})

function fill(s) {
  shop.value = s
  name.value = s.name ?? ''
  phone.value = s.phone ?? ''
  description.value = s.description ?? ''
  available.value = Boolean(s.is_available)
}

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    fill(await shopApi.getShop())
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
  const n = name.value.trim()
  if (!n) errors.name = clientError('shop.errors.nameRequired')
  else if (n.length < 2) errors.name = clientError('shop.errors.nameShort')
  // The shop phone is optional, unlike the account phone.
  if (phone.value.trim() && phoneProblem(phone.value))
    errors.phone = clientError('auth.register.errors.phoneInvalid')
  if (description.value.length > 500)
    errors.description = clientError('shop.errors.descriptionLong')
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
    fill(
      await shopApi.updateShop({
        name: name.value.trim(),
        phone: phone.value.trim(),
        description: description.value.trim(),
        is_available: available.value,
      }),
    )
    saved.value = true
  } catch (err) {
    fieldErrors.value = serverFieldErrors(err, ['name', 'phone', 'description', 'is_available'])
    if (Object.keys(fieldErrors.value).length === 0) formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <h1>{{ t('shop.title') }}</h1>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />

    <template v-if="!loading && !loadError">
      <p v-if="saved" class="form-notice" role="status" data-test="saved">{{ t('shop.saved') }}</p>
      <p v-if="formError" class="form-error" role="alert" data-test="form-error">
        {{ formError }}
      </p>

      <p v-if="shop.can_accept_orders" class="form-notice" role="status" data-test="orderable-yes">
        {{ t('shop.orderable') }}
      </p>
      <div v-else class="form-notice" data-test="orderable-no">
        <p>{{ t('shop.notOrderable') }}</p>
        <ul>
          <li v-if="!shop.is_available" data-test="why-closed">{{ t('shop.whyClosed') }}</li>
          <li v-else data-test="why-pickup">
            {{ t('shop.whyPickup') }}
            <RouterLink to="/trader/locations">{{ t('trader.nav.locations') }}</RouterLink>
          </li>
        </ul>
      </div>

      <form class="app-form" novalidate data-test="form" @submit.prevent="submit">
        <FormField
          id="shop-name"
          name="name"
          :label="t('shop.name')"
          :model-value="name"
          :error="msg(fieldErrors.name)"
          :disabled="submitting"
          required
          @update:model-value="name = $event"
        />
        <FormField
          id="shop-phone"
          name="phone"
          type="tel"
          inputmode="tel"
          dir="ltr"
          :label="t('shop.phone')"
          :hint="t('shop.phoneHint')"
          :model-value="phone"
          :error="msg(fieldErrors.phone)"
          :disabled="submitting"
          @update:model-value="phone = $event"
        />
        <div class="field">
          <label for="shop-description">{{ t('shop.description') }}</label>
          <textarea
            id="shop-description"
            v-model="description"
            rows="3"
            maxlength="500"
            dir="auto"
            :disabled="submitting"
            :aria-invalid="fieldErrors.description ? 'true' : 'false'"
          />
          <p v-if="fieldErrors.description" class="field-error" role="alert">
            {{ msg(fieldErrors.description) }}
          </p>
        </div>
        <label class="check">
          <input v-model="available" type="checkbox" data-test="available" :disabled="submitting" />
          {{ t('shop.available') }}
        </label>
        <div class="btn-row">
          <button
            type="submit"
            class="btn btn-primary"
            data-test="save"
            :disabled="submitting"
            :aria-busy="submitting"
          >
            {{ submitting ? t('account.profile.saving') : t('account.profile.save') }}
          </button>
        </div>
      </form>
    </template>
  </section>
</template>

<style scoped>
.field {
  display: grid;
  gap: 0.375rem;
}
label {
  font-weight: 600;
}
textarea {
  font: inherit;
  padding: 0.5rem 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
  color: inherit;
  resize: vertical;
}
.check {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-block-size: var(--touch-target);
}
.check input {
  inline-size: 1.25rem;
  block-size: 1.25rem;
}
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
</style>
