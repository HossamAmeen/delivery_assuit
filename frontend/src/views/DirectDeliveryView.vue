<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import PlaceChooser from '@/components/PlaceChooser.vue'
import * as addressesApi from '@/api/addresses'
import * as ordersApi from '@/api/orders'
import { clientError, errorText, formMessage, serverFieldErrors } from '@/utils/forms'
import { choicePayload, choiceProblems, emptyChoice } from '@/utils/places'

const { t } = useI18n()
const msg = (e) => errorText(e, t)

const addresses = ref([])
const pickup = ref(emptyChoice(false))
const delivery = ref(emptyChoice(false))
const description = ref('')
const fieldErrors = ref({})
const formError = ref('')
const submitting = ref(false)
const created = ref(null)

onMounted(async () => {
  // Saved addresses are a convenience; typing a place always works.
  try {
    addresses.value = (await addressesApi.listAddresses({ page_size: 100 })).results
  } catch {
    addresses.value = []
  }
  const has = addresses.value.length > 0
  pickup.value = emptyChoice(has)
  delivery.value = emptyChoice(has)
})

const prefixed = (prefix, problems) =>
  Object.fromEntries(Object.entries(problems).map(([k, v]) => [`${prefix}.${k}`, v]))

function validate() {
  const errors = {
    ...prefixed('pickup', choiceProblems(pickup.value)),
    ...prefixed('delivery', choiceProblems(delivery.value)),
  }
  const text = description.value.trim()
  if (!text) errors.description = clientError('client.direct.errors.detailsRequired')
  else if (text.length < 3) errors.description = clientError('client.direct.errors.detailsShort')
  else if (text.length > 1000) errors.description = clientError('client.direct.errors.detailsLong')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

// Server place errors arrive nested under pickup/delivery, or as <side>_saved_address.
function mapServerErrors(err) {
  const raw = serverFieldErrors(err, [
    'description',
    'pickup',
    'delivery',
    'pickup_saved_address',
    'delivery_saved_address',
  ])
  const out = { description: raw.description }
  for (const side of ['pickup', 'delivery']) {
    const nested = err?.errors?.[side]
    if (nested && !Array.isArray(nested) && typeof nested === 'object') {
      for (const [k, v] of Object.entries(nested)) out[`${side}.${k}`] = [].concat(v).join(' ')
    } else if (raw[side]) out[`${side}.general`] = raw[side]
    if (raw[`${side}_saved_address`]) out[`${side}.savedId`] = raw[`${side}_saved_address`]
  }
  return Object.fromEntries(Object.entries(out).filter(([, v]) => v))
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  if (!validate()) return
  submitting.value = true
  try {
    created.value = await ordersApi.createOrder({
      ...choicePayload(pickup.value, 'pickup'),
      ...choicePayload(delivery.value, 'delivery'),
      description: description.value.trim(),
    })
  } catch (err) {
    fieldErrors.value = mapServerErrors(err)
    if (Object.keys(fieldErrors.value).length === 0) formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}

const sideErrors = (side) =>
  computed(() =>
    Object.fromEntries(
      Object.entries(fieldErrors.value)
        .filter(([k]) => k.startsWith(`${side}.`))
        .map(([k, v]) => [k.slice(side.length + 1), msg(v)]),
    ),
  )
const pickupErrors = sideErrors('pickup')
const deliveryErrors = sideErrors('delivery')
</script>

<template>
  <section class="form-page">
    <div v-if="created" data-test="confirmation">
      <h1>{{ t('client.order.doneTitle') }}</h1>
      <p role="status">{{ t('client.order.doneIntro') }}</p>
      <p>
        {{ t('client.order.reference') }}:
        <strong dir="ltr" data-test="reference">{{ created.reference }}</strong>
      </p>
      <p>{{ t('client.order.waitingReview') }}</p>
      <p>
        <RouterLink to="/client" class="touch-link">{{ t('nav.backHome') }}</RouterLink>
      </p>
    </div>

    <template v-else>
      <h1>{{ t('client.direct.title') }}</h1>
      <p v-if="formError" class="form-error" role="alert" data-test="form-error">{{ formError }}</p>

      <form class="app-form" novalidate data-test="form" @submit.prevent="submit">
        <PlaceChooser
          v-model="pickup"
          :legend="t('client.direct.pickup')"
          :addresses="addresses"
          :errors="pickupErrors"
          :disabled="submitting"
          id-prefix="dir-pick"
        />
        <p v-if="fieldErrors['pickup.general']" class="field-error" role="alert">
          {{ msg(fieldErrors['pickup.general']) }}
        </p>

        <PlaceChooser
          v-model="delivery"
          :legend="t('client.direct.delivery')"
          :addresses="addresses"
          :errors="deliveryErrors"
          :disabled="submitting"
          id-prefix="dir-del"
        />
        <p v-if="fieldErrors['delivery.general']" class="field-error" role="alert">
          {{ msg(fieldErrors['delivery.general']) }}
        </p>

        <div class="field">
          <label for="dir-description">
            {{ t('client.direct.details') }}<span class="required-mark" aria-hidden="true"> *</span>
          </label>
          <textarea
            id="dir-description"
            v-model="description"
            rows="3"
            maxlength="1000"
            dir="auto"
            required
            aria-required="true"
            :disabled="submitting"
            :aria-invalid="fieldErrors.description ? 'true' : 'false'"
          />
          <p
            v-if="fieldErrors.description"
            class="field-error"
            role="alert"
            data-test="description-error"
          >
            {{ msg(fieldErrors.description) }}
          </p>
        </div>

        <div class="btn-row">
          <button
            type="submit"
            class="btn btn-primary"
            data-test="submit"
            :disabled="submitting"
            :aria-busy="submitting"
          >
            {{ submitting ? t('client.order.submitting') : t('client.order.submit') }}
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
}
.required-mark {
  color: #b42318;
}
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
</style>
