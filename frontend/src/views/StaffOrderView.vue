<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as ordersApi from '@/api/orders'
import { ApiError } from '@/api/http'
import { clientError, errorText, formMessage, serverFieldErrors } from '@/utils/forms'
import { formatDateTime } from '@/utils/format'

// One order for Admin and Manager (BL-054): details, timeline, fee, cancel, and where to act.
const { t, locale } = useI18n()
const msg = (e) => errorText(e, t)
const route = useRoute()
const id = computed(() => route.params.id)

const order = ref(null)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const missing = ref(false)
const notice = ref('')
const actionError = ref('')

const fee = ref('')
const feeError = ref(null)
const cancelling = ref(false)
const reason = ref('')
const reasonError = ref(null)
const busy = ref(false)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  missing.value = false
  try {
    order.value = await ordersApi.getOrder(id.value)
    fee.value = order.value.delivery_fee === null ? '' : String(order.value.delivery_fee)
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

const finished = computed(() => ['delivered', 'cancelled'].includes(order.value?.status))
const place = (p) => `${p.name} — ${p.address}`

// The detail carries the timeline, the action responses do not, so reload after a change.
async function saveFee() {
  if (busy.value) return
  actionError.value = ''
  notice.value = ''
  const text = fee.value.trim()
  const n = Number(text)
  if (!text || !Number.isFinite(n) || n < 0 || n > 100000 || !/^\d+(\.\d{1,2})?$/.test(text)) {
    feeError.value = clientError('admin.orders.errors.feeInvalid')
    return
  }
  feeError.value = null
  busy.value = true
  try {
    await ordersApi.setFee(order.value.id, n)
    notice.value = t('staffOrder.feeSaved')
    await load()
  } catch (err) {
    const f = serverFieldErrors(err, ['delivery_fee', 'status'])
    feeError.value = f.delivery_fee ?? null
    if (!feeError.value) actionError.value = f.status || formMessage(err, t)
    if (err?.status === 400) await load()
  } finally {
    busy.value = false
  }
}

async function confirmCancel() {
  if (busy.value) return
  actionError.value = ''
  notice.value = ''
  const text = reason.value.trim()
  if (text.length < 3) {
    reasonError.value = clientError('admin.orders.errors.reasonShort')
    return
  }
  reasonError.value = null
  busy.value = true
  try {
    await ordersApi.cancelOrder(order.value.id, text)
    cancelling.value = false
    reason.value = ''
    notice.value = t('staffOrder.cancelled')
    await load()
  } catch (err) {
    const f = serverFieldErrors(err, ['reason', 'status'])
    reasonError.value = f.reason ?? null
    if (!reasonError.value) actionError.value = f.status || formMessage(err, t)
    if (err?.status === 400 && !f.reason) await load()
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <p>
      <RouterLink to="/admin/orders" class="touch-link">{{ t('staffOrder.back') }}</RouterLink>
    </p>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />
    <div v-if="missing" class="form-notice" role="status" data-test="missing">
      {{ t('orders.notFound') }}
    </div>

    <template v-if="order && !loading">
      <h1 dir="ltr" data-test="reference">{{ order.reference }}</h1>
      <p>
        <span class="role-badge" data-test="status">{{ t(`orders.status.${order.status}`) }}</span>
      </p>
      <p v-if="notice" class="form-notice" role="status" data-test="notice">{{ notice }}</p>
      <p v-if="actionError" class="form-error" role="alert" data-test="action-error">
        {{ actionError }}
      </p>

      <dl class="details">
        <div>
          <dt>{{ t('admin.orders.client') }}</dt>
          <dd>
            {{ order.client.full_name }}
            <span v-if="order.client.phone" dir="ltr" data-test="client-phone">{{
              order.client.phone
            }}</span>
          </dd>
        </div>
        <div v-if="order.shop">
          <dt>{{ t('orders.shop') }}</dt>
          <dd>
            {{ order.shop.name }}
            <span v-if="order.shop.phone" dir="ltr">{{ order.shop.phone }}</span>
          </dd>
        </div>
        <div v-if="order.driver">
          <dt>{{ t('admin.table.driver') }}</dt>
          <dd data-test="driver">{{ order.driver.full_name }}</dd>
        </div>
        <div>
          <dt>{{ t('admin.orders.pickup') }}</dt>
          <dd>{{ place(order.pickup) }}</dd>
        </div>
        <div>
          <dt>{{ t('admin.orders.delivery') }}</dt>
          <dd>{{ place(order.delivery) }}</dd>
        </div>
        <div v-if="order.description">
          <dt>{{ t('admin.orders.description') }}</dt>
          <dd>{{ order.description }}</dd>
        </div>
        <div v-if="order.items.length">
          <dt>{{ t('admin.orders.items') }}</dt>
          <dd>
            <ul class="lines">
              <li v-for="(line, i) in order.items" :key="i" data-test="line">
                {{ line.quantity }} × {{ line.name }}
                <span v-if="line.price !== null" data-test="line-price">({{ line.price }})</span>
              </li>
            </ul>
            <span v-if="order.items_total !== null" data-test="items-total"
              >{{ t('staffOrder.itemsTotal') }}: {{ order.items_total }}</span
            >
          </dd>
        </div>
        <div>
          <dt>{{ t('admin.table.fee') }}</dt>
          <dd data-test="fee">
            {{ order.delivery_fee === null ? t('staffOrder.noFee') : order.delivery_fee }}
          </dd>
        </div>
        <div v-if="order.cancel_reason">
          <dt>{{ t('orders.cancelReason') }}</dt>
          <dd data-test="cancel-reason">{{ order.cancel_reason }}</dd>
        </div>
      </dl>

      <div v-if="!finished" class="actions">
        <RouterLink
          v-if="order.status === 'created'"
          to="/admin/orders/review"
          class="btn btn-primary touch-link"
          data-test="go-review"
          >{{ t('staffOrder.review') }}</RouterLink
        >
        <RouterLink
          v-if="order.status === 'available'"
          to="/admin/orders/assign"
          class="btn btn-primary touch-link"
          data-test="go-assign"
          >{{ t('staffOrder.assign') }}</RouterLink
        >

        <div class="field">
          <label for="fee">{{ t('staffOrder.setFee') }}</label>
          <div class="row">
            <input
              id="fee"
              v-model="fee"
              type="text"
              inputmode="decimal"
              dir="ltr"
              :disabled="busy"
              :aria-invalid="feeError ? 'true' : 'false'"
              data-test="fee-input"
            />
            <button
              type="button"
              class="btn"
              data-test="save-fee"
              :disabled="busy"
              @click="saveFee"
            >
              {{ t('account.profile.save') }}
            </button>
          </div>
          <p v-if="feeError" class="field-error" role="alert" data-test="fee-error">
            {{ msg(feeError) }}
          </p>
        </div>

        <div v-if="cancelling" class="field">
          <label for="cancel-reason">{{ t('admin.orders.reason') }}</label>
          <input
            id="cancel-reason"
            v-model="reason"
            type="text"
            maxlength="500"
            :disabled="busy"
            :aria-invalid="reasonError ? 'true' : 'false'"
            data-test="cancel-reason-input"
          />
          <p v-if="reasonError" class="field-error" role="alert" data-test="reason-error">
            {{ msg(reasonError) }}
          </p>
          <div class="btn-row">
            <button
              type="button"
              class="btn btn-danger"
              data-test="confirm-cancel"
              :disabled="busy"
              @click="confirmCancel"
            >
              {{ t('staffOrder.confirmCancel') }}
            </button>
            <button type="button" class="btn" data-test="keep" @click="cancelling = false">
              {{ t('common.cancel') }}
            </button>
          </div>
        </div>
        <button
          v-else
          type="button"
          class="btn btn-danger"
          data-test="cancel"
          @click="cancelling = true"
        >
          {{ t('staffOrder.cancel') }}
        </button>
      </div>

      <h2>{{ t('staffOrder.timeline') }}</h2>
      <ol class="timeline" data-test="timeline">
        <li v-for="(h, i) in order.history" :key="i" data-test="step">
          <strong>{{ t(`orders.status.${h.to_status}`) }}</strong>
          <span>{{ formatDateTime(h.created_at, locale) }}</span>
          <span>{{ h.actor_name }}</span>
          <span v-if="h.reason" class="reason">{{ h.reason }}</span>
        </li>
      </ol>
    </template>
  </section>
</template>

<style scoped>
.details {
  display: grid;
  gap: 0.75rem;
  margin: 1rem 0;
}
.details div {
  display: grid;
  gap: 0.125rem;
}
dt {
  font-weight: 600;
}
dd {
  display: grid;
  gap: 0.25rem;
  margin: 0;
  overflow-wrap: anywhere;
}
.lines {
  margin: 0;
  padding-inline-start: 1.25rem;
}
.actions {
  display: grid;
  gap: 0.75rem;
  margin-block-end: 1rem;
}
.field {
  display: grid;
  gap: 0.375rem;
}
.row {
  display: flex;
  gap: 0.5rem;
}
label {
  font-weight: 600;
}
input {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
}
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
.timeline {
  display: grid;
  gap: 0.5rem;
  padding-inline-start: 1.25rem;
}
.timeline li {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.75rem;
}
.reason {
  font-style: italic;
}
.btn {
  text-decoration: none;
}
</style>
