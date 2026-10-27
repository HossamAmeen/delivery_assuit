<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import PlaceChooser from '@/components/PlaceChooser.vue'
import * as addressesApi from '@/api/addresses'
import * as ordersApi from '@/api/orders'
import * as shopsApi from '@/api/shops'
import { ApiError } from '@/api/http'
import { clientError, errorText, formMessage, serverFieldErrors } from '@/utils/forms'
import { choicePayload, choiceProblems, emptyChoice, placeToForm } from '@/utils/places'

// Edit an order before a driver is assigned (BL-026, BR-13).
const { t } = useI18n()
const msg = (e) => errorText(e, t)
const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id)

const order = ref(null)
const shop = ref(null) // the shop's current items and pickup places, when it is still orderable
const shopGone = ref(false)
const addresses = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const missing = ref(false)

const description = ref('')
const pickup = ref(emptyChoice(false))
const delivery = ref(emptyChoice(false))
const pickupId = ref('')
const changeItems = ref(false)
const quantities = ref({})
const fieldErrors = ref({})
const formError = ref('')
const submitting = ref(false)

const isShopOrder = computed(() => Boolean(order.value?.shop))
const editable = computed(() => ['created', 'available'].includes(order.value?.status))

const typed = (place) => ({ mode: 'typed', savedId: '', place: placeToForm(place) })

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  missing.value = false
  try {
    const o = await ordersApi.getOrder(id.value)
    order.value = o
    description.value = o.description ?? ''
    delivery.value = typed(o.delivery)
    pickup.value = typed(o.pickup)
    try {
      addresses.value = (await addressesApi.listAddresses({ page_size: 100 })).results
    } catch {
      addresses.value = []
    }
    if (o.shop) {
      try {
        shop.value = await shopsApi.getShop(o.shop.id)
        // The order stores line names, so match the current items by name.
        const byName = Object.fromEntries(o.items.map((l) => [l.name.toLowerCase(), l.quantity]))
        quantities.value = Object.fromEntries(
          shop.value.items.map((i) => [i.id, String(byName[i.name.toLowerCase()] ?? '')]),
        )
      } catch (err) {
        // A shop that closed since can still have its delivery place edited.
        if (err instanceof ApiError && err.status === 404) shopGone.value = true
        else throw err
      }
    }
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) missing.value = true
    else {
      offline.value = Boolean(err?.isNetworkError)
      loadError.value = formMessage(err, t)
    }
  } finally {
    loading.value = false
  }
}
onMounted(load)

const qty = (itemId) => {
  const n = Number.parseInt(quantities.value[itemId], 10)
  return Number.isFinite(n) && n > 0 ? n : 0
}
const lines = computed(() =>
  (shop.value?.items ?? [])
    .filter((i) => qty(i.id) > 0)
    .map((i) => ({ item: i.id, quantity: qty(i.id) })),
)

function validate() {
  const errors = {}
  const text = description.value.trim()
  if (!isShopOrder.value && text.length < 3)
    errors.description = clientError('client.direct.errors.detailsShort')
  if (text.length > 1000) errors.description = clientError('client.order.errors.descriptionLong')
  if (changeItems.value && lines.value.length === 0)
    errors.items = clientError('client.order.errors.itemsRequired')
  const prefixed = (side, problems) =>
    Object.fromEntries(Object.entries(problems).map(([k, v]) => [`${side}.${k}`, v]))
  Object.assign(errors, prefixed('delivery', choiceProblems(delivery.value)))
  if (!isShopOrder.value) Object.assign(errors, prefixed('pickup', choiceProblems(pickup.value)))
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

function mapServerErrors(err) {
  const raw = serverFieldErrors(err, [
    'description',
    'items',
    'pickup_location',
    'pickup',
    'delivery',
    'pickup_saved_address',
    'delivery_saved_address',
    'status',
  ])
  const out = { ...raw }
  for (const side of ['pickup', 'delivery']) {
    const nested = err?.errors?.[side]
    if (nested && !Array.isArray(nested) && typeof nested === 'object') {
      delete out[side]
      for (const [k, v] of Object.entries(nested)) out[`${side}.${k}`] = [].concat(v).join(' ')
    }
    if (raw[`${side}_saved_address`]) {
      out[`${side}.savedId`] = raw[`${side}_saved_address`]
      delete out[`${side}_saved_address`]
    }
  }
  return out
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  if (!validate()) return
  submitting.value = true
  const body = {
    description: description.value.trim(),
    ...choicePayload(delivery.value, 'delivery'),
  }
  if (isShopOrder.value) {
    if (pickupId.value) body.pickup_location = Number(pickupId.value)
    if (changeItems.value) body.items = lines.value
  } else {
    Object.assign(body, choicePayload(pickup.value, 'pickup'))
  }
  try {
    await ordersApi.updateOrder(order.value.id, body)
    await router.push(`/client/orders/${order.value.id}`)
  } catch (err) {
    fieldErrors.value = mapServerErrors(err)
    const status = fieldErrors.value.status
    if (status) formError.value = status
    else if (Object.keys(fieldErrors.value).length === 0) formError.value = formMessage(err, t)
    // Refused because a driver was assigned meanwhile: show the real state.
    if (err?.status === 403) {
      formError.value = formMessage(err, t)
      await load()
    }
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
    <p>
      <RouterLink :to="`/client/orders/${id}`" class="touch-link">{{
        t('clientOrder.backToOrder')
      }}</RouterLink>
    </p>
    <h1>{{ t('clientOrder.editTitle') }}</h1>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />
    <div v-if="missing" class="form-notice" role="status" data-test="missing">
      {{ t('orders.notFound') }}
    </div>

    <template v-if="order && !loading">
      <p v-if="!editable" class="form-notice" role="status" data-test="locked">
        {{ t('clientOrder.locked') }}
      </p>

      <form v-else class="app-form" novalidate data-test="form" @submit.prevent="submit">
        <p v-if="order.status === 'available'" class="form-notice" data-test="rereview">
          {{ t('clientOrder.rereview') }}
        </p>
        <p v-if="formError" class="form-error" role="alert" data-test="form-error">
          {{ formError }}
        </p>

        <template v-if="isShopOrder">
          <p v-if="shopGone" class="form-notice" data-test="shop-gone">
            {{ t('clientOrder.shopGone') }}
          </p>
          <template v-else-if="shop">
            <label class="check">
              <input
                v-model="changeItems"
                type="checkbox"
                data-test="change-items"
                :disabled="submitting"
              />
              {{ t('clientOrder.changeItems') }}
            </label>
            <fieldset v-if="changeItems" class="items">
              <legend>{{ t('client.shops.items') }}</legend>
              <div v-for="item in shop.items" :key="item.id" class="line" data-test="line">
                <label :for="`qty-${item.id}`">{{ item.name }}</label>
                <input
                  :id="`qty-${item.id}`"
                  v-model="quantities[item.id]"
                  type="number"
                  min="0"
                  max="99"
                  inputmode="numeric"
                  dir="ltr"
                  :disabled="submitting"
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
                <option value="">{{ t('clientOrder.keepPickup') }}</option>
                <option v-for="p in shop.pickup_locations" :key="p.id" :value="String(p.id)">
                  {{ p.name }} — {{ p.address }}
                </option>
              </select>
            </div>
          </template>
        </template>
        <PlaceChooser
          v-else
          v-model="pickup"
          :legend="t('client.direct.pickup')"
          :addresses="addresses"
          :errors="pickupErrors"
          :disabled="submitting"
          id-prefix="edit-pick"
        />

        <PlaceChooser
          v-model="delivery"
          :legend="t('client.order.delivery')"
          :addresses="addresses"
          :errors="deliveryErrors"
          :disabled="submitting"
          id-prefix="edit-del"
        />

        <div class="field">
          <label for="edit-description">{{
            isShopOrder ? t('client.order.note') : t('client.direct.details')
          }}</label>
          <textarea
            id="edit-description"
            v-model="description"
            rows="3"
            maxlength="1000"
            dir="auto"
            :disabled="submitting"
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
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
</style>
