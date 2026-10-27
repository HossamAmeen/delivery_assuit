<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import PlaceChooser from '@/components/PlaceChooser.vue'
import * as addressesApi from '@/api/addresses'
import * as ordersApi from '@/api/orders'
import * as shopsApi from '@/api/shops'
import { ApiError } from '@/api/http'
import { clientError, errorText, formMessage, serverFieldErrors } from '@/utils/forms'
import { choicePayload, choiceProblems, emptyChoice } from '@/utils/places'

const { t } = useI18n()
const msg = (e) => errorText(e, t)
const route = useRoute()
const shopId = computed(() => route.params.id)

const shop = ref(null)
const addresses = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const unavailable = ref(false)

// quantity per item id, as text from the number inputs ('' or '0' means not ordered)
const quantities = ref({})
const pickupId = ref('')
const delivery = ref(emptyChoice(false))
const description = ref('')
const fieldErrors = ref({})
const formError = ref('')
const submitting = ref(false)
const created = ref(null)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  unavailable.value = false
  try {
    shop.value = await shopsApi.getShop(shopId.value)
    // Saved addresses are a convenience: if they fail to load, the client can still type a place.
    try {
      addresses.value = (await addressesApi.listAddresses({ page_size: 100 })).results
    } catch {
      addresses.value = []
    }
    delivery.value = emptyChoice(addresses.value.length > 0)
    const def = shop.value.pickup_locations.find((p) => p.is_default)
    pickupId.value = String((def ?? shop.value.pickup_locations[0])?.id ?? '')
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) unavailable.value = true
    else {
      offline.value = Boolean(err?.isNetworkError)
      loadError.value = formMessage(err, t)
    }
  } finally {
    loading.value = false
  }
}
onMounted(load)

const qty = (id) => {
  const n = Number.parseInt(quantities.value[id], 10)
  return Number.isFinite(n) && n > 0 ? n : 0
}
const lines = computed(() =>
  (shop.value?.items ?? [])
    .filter((i) => qty(i.id) > 0)
    .map((i) => ({ item: i.id, quantity: qty(i.id) })),
)

function validate() {
  const errors = {}
  if (lines.value.length === 0) errors.items = clientError('client.order.errors.itemsRequired')
  if (lines.value.some((l) => l.quantity > 99))
    errors.items = clientError('client.order.errors.quantityMax')
  Object.assign(
    errors,
    Object.fromEntries(
      Object.entries(choiceProblems(delivery.value)).map(([k, v]) => [`delivery.${k}`, v]),
    ),
  )
  if (description.value.length > 1000)
    errors.description = clientError('client.order.errors.descriptionLong')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

// Server errors for the delivery place arrive under 'delivery' (typed) or 'delivery_saved_address'.
function mapServerErrors(err) {
  const raw = serverFieldErrors(err, [
    'items',
    'description',
    'pickup_location',
    'delivery',
    'delivery_saved_address',
    'shop',
  ])
  const out = { ...raw }
  const nested = err?.errors?.delivery
  if (nested && !Array.isArray(nested) && typeof nested === 'object') {
    delete out.delivery
    for (const [k, v] of Object.entries(nested)) out[`delivery.${k}`] = [].concat(v).join(' ')
  }
  if (raw.delivery_saved_address) {
    out['delivery.savedId'] = raw.delivery_saved_address
    delete out.delivery_saved_address
  }
  return out
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  if (!validate()) return
  submitting.value = true
  const body = {
    shop: shop.value.id,
    items: lines.value,
    ...choicePayload(delivery.value, 'delivery'),
  }
  if (pickupId.value) body.pickup_location = Number(pickupId.value)
  if (description.value.trim()) body.description = description.value.trim()
  try {
    created.value = await ordersApi.createOrder(body)
  } catch (err) {
    fieldErrors.value = mapServerErrors(err)
    // A closed shop surfaces on `shop`; show it as the page message, not under a field.
    if (fieldErrors.value.shop) {
      formError.value = fieldErrors.value.shop
      delete fieldErrors.value.shop
    } else if (Object.keys(fieldErrors.value).length === 0) formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}

const deliveryErrors = computed(() =>
  Object.fromEntries(
    Object.entries(fieldErrors.value)
      .filter(([k]) => k.startsWith('delivery.'))
      .map(([k, v]) => [k.slice('delivery.'.length), msg(v)]),
  ),
)
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
      <p>
        <RouterLink :to="`/client/shops/${shopId}`" class="touch-link">{{
          t('client.order.back')
        }}</RouterLink>
      </p>
      <h1>{{ t('client.order.title') }}</h1>

      <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />
      <div v-if="unavailable" class="form-notice" role="status" data-test="unavailable">
        {{ t('client.shops.unavailable') }}
      </div>

      <form
        v-if="shop && !loading"
        class="app-form"
        novalidate
        data-test="form"
        @submit.prevent="submit"
      >
        <h2>{{ shop.name }}</h2>
        <p v-if="formError" class="form-error" role="alert" data-test="form-error">
          {{ formError }}
        </p>

        <fieldset class="items">
          <legend>{{ t('client.shops.items') }}</legend>
          <div v-for="item in shop.items" :key="item.id" class="line" data-test="line">
            <label :for="`qty-${item.id}`">
              {{ item.name }}
              <span v-if="item.price !== null && item.price !== undefined" class="price">{{
                item.price
              }}</span>
            </label>
            <input
              :id="`qty-${item.id}`"
              v-model="quantities[item.id]"
              type="number"
              min="0"
              max="99"
              inputmode="numeric"
              dir="ltr"
              :disabled="submitting"
              :aria-label="`${t('client.order.quantity')}: ${item.name}`"
              :data-test="`qty-${item.id}`"
            />
          </div>
          <p v-if="fieldErrors.items" class="field-error" role="alert" data-test="items-error">
            {{ msg(fieldErrors.items) }}
          </p>
        </fieldset>

        <div v-if="shop.pickup_locations.length > 1" class="field">
          <label for="pickup">{{ t('client.order.pickup') }}</label>
          <select id="pickup" v-model="pickupId" :disabled="submitting" data-test="pickup">
            <option v-for="p in shop.pickup_locations" :key="p.id" :value="String(p.id)">
              {{ p.name }} — {{ p.address }}
            </option>
          </select>
          <p v-if="fieldErrors.pickup_location" class="field-error" role="alert">
            {{ msg(fieldErrors.pickup_location) }}
          </p>
        </div>
        <p v-else-if="shop.pickup_locations.length" data-test="pickup-fixed">
          {{ t('client.order.pickup') }}: {{ shop.pickup_locations[0].name }} —
          {{ shop.pickup_locations[0].address }}
        </p>

        <PlaceChooser
          v-model="delivery"
          :legend="t('client.order.delivery')"
          :addresses="addresses"
          :errors="deliveryErrors"
          :disabled="submitting"
          id-prefix="ord-del"
        />
        <p v-if="fieldErrors.delivery" class="field-error" role="alert">
          {{ msg(fieldErrors.delivery) }}
        </p>

        <div class="field">
          <label for="ord-description">{{ t('client.order.note') }}</label>
          <textarea
            id="ord-description"
            v-model="description"
            rows="3"
            maxlength="1000"
            dir="auto"
            :disabled="submitting"
          />
          <p v-if="fieldErrors.description" class="field-error" role="alert">
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
.items {
  display: grid;
  gap: 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
}
.line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}
.line input {
  inline-size: 5rem;
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.5rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
}
.field {
  display: grid;
  gap: 0.375rem;
}
label {
  font-weight: 600;
}
select,
textarea {
  font: inherit;
  padding: 0.5rem 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
  color: inherit;
}
select {
  min-block-size: var(--touch-target);
}
.price {
  margin-inline-start: 0.5rem;
  font-weight: 400;
}
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
</style>
