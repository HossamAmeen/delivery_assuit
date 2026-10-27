<script setup>
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ListStatus from '@/components/ListStatus.vue'
import * as ordersApi from '@/api/orders'
import { clientError, errorText, formMessage, serverFieldErrors } from '@/utils/forms'

const { t } = useI18n()
const msg = (e) => errorText(e, t)

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const busyId = ref(null)
const actionError = ref('')
const doneNotice = ref('')

// Per-order form state: which panel is open and what was typed.
const openId = ref(null)
const mode = ref('') // 'approve' | 'reject'
const fee = ref('')
const reason = ref('')
const fieldErrors = ref({})

// `silent` refreshes quietly (auto-refresh): no spinner, errors are ignored so the screen stays.
async function load({ silent = false } = {}) {
  if (!silent) loading.value = true
  if (!silent) loadError.value = ''
  if (!silent) offline.value = false
  try {
    rows.value = (await ordersApi.listOrders({ status: 'created', page_size: 100 })).results
  } catch (err) {
    if (silent) return
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    if (!silent) loading.value = false
  }
}
onMounted(load)
useAutoRefresh(() => load({ silent: true }))

function open(id, which) {
  openId.value = id
  mode.value = which
  fee.value = ''
  reason.value = ''
  fieldErrors.value = {}
  actionError.value = ''
  doneNotice.value = ''
}
function close() {
  openId.value = null
  mode.value = ''
}

function validate() {
  const errors = {}
  if (mode.value === 'approve' && fee.value.trim() !== '') {
    const n = Number(fee.value.trim())
    if (!Number.isFinite(n) || n < 0 || n > 100000 || !/^\d+(\.\d{1,2})?$/.test(fee.value.trim()))
      errors.delivery_fee = clientError('admin.orders.errors.feeInvalid')
  }
  if (mode.value === 'reject') {
    const r = reason.value.trim()
    if (!r) errors.reason = clientError('admin.orders.errors.reasonRequired')
    else if (r.length < 3) errors.reason = clientError('admin.orders.errors.reasonShort')
  }
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function confirm(row) {
  if (busyId.value) return
  actionError.value = ''
  if (!validate()) return
  busyId.value = row.id
  try {
    if (mode.value === 'approve') {
      const f = fee.value.trim()
      await ordersApi.approveOrder(row.id, f === '' ? null : Number(f))
      doneNotice.value = t('admin.orders.approved', { reference: row.reference })
    } else {
      await ordersApi.rejectOrder(row.id, reason.value.trim())
      doneNotice.value = t('admin.orders.rejected', { reference: row.reference })
    }
    rows.value = rows.value.filter((r) => r.id !== row.id)
    close()
  } catch (err) {
    fieldErrors.value = serverFieldErrors(err, ['delivery_fee', 'reason'])
    if (Object.keys(fieldErrors.value).length === 0) {
      actionError.value = formMessage(err, t)
      // Someone else already reviewed it: the row is stale, so refresh the queue.
      if (err?.status === 400) await load()
    }
  } finally {
    busyId.value = null
  }
}

const place = (p) => `${p.name} — ${p.address}`
</script>

<template>
  <section>
    <h1>{{ t('admin.orders.title') }}</h1>
    <p v-if="doneNotice" class="form-notice" role="status" data-test="done">{{ doneNotice }}</p>
    <p v-if="actionError" class="form-error" role="alert" data-test="action-error">
      {{ actionError }}
    </p>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('admin.orders.empty')"
      @retry="load"
    />

    <ul v-if="!loading && !loadError && rows.length" class="review-list">
      <li v-for="row in rows" :key="row.id" class="review-row" data-test="row">
        <div class="head">
          <strong dir="ltr" data-test="reference">{{ row.reference }}</strong>
          <span class="role-badge">{{ row.shop ? row.shop.name : t('admin.orders.direct') }}</span>
        </div>
        <dl class="details">
          <div>
            <dt>{{ t('admin.orders.client') }}</dt>
            <dd>
              {{ row.client.full_name }}
              <span v-if="row.client.phone" dir="ltr">{{ row.client.phone }}</span>
            </dd>
          </div>
          <div>
            <dt>{{ t('admin.orders.pickup') }}</dt>
            <dd data-test="pickup">{{ place(row.pickup) }}</dd>
          </div>
          <div>
            <dt>{{ t('admin.orders.delivery') }}</dt>
            <dd data-test="delivery">{{ place(row.delivery) }}</dd>
          </div>
          <div v-if="row.items.length">
            <dt>{{ t('admin.orders.items') }}</dt>
            <dd>
              <ul class="lines">
                <li v-for="(line, i) in row.items" :key="i" data-test="line">
                  {{ line.quantity }} × {{ line.name }}
                </li>
              </ul>
            </dd>
          </div>
          <div v-if="row.description">
            <dt>{{ t('admin.orders.description') }}</dt>
            <dd data-test="description">{{ row.description }}</dd>
          </div>
        </dl>

        <div v-if="openId === row.id" class="panel">
          <div v-if="mode === 'approve'" class="field">
            <label :for="`fee-${row.id}`">{{ t('admin.orders.fee') }}</label>
            <input
              :id="`fee-${row.id}`"
              v-model="fee"
              type="text"
              inputmode="decimal"
              dir="ltr"
              :disabled="busyId === row.id"
              :aria-invalid="fieldErrors.delivery_fee ? 'true' : 'false'"
              data-test="fee"
            />
            <p class="hint">{{ t('admin.orders.feeHint') }}</p>
            <p
              v-if="fieldErrors.delivery_fee"
              class="field-error"
              role="alert"
              data-test="fee-error"
            >
              {{ msg(fieldErrors.delivery_fee) }}
            </p>
          </div>
          <div v-else class="field">
            <label :for="`reason-${row.id}`">{{ t('admin.orders.reason') }}</label>
            <input
              :id="`reason-${row.id}`"
              v-model="reason"
              type="text"
              maxlength="500"
              :disabled="busyId === row.id"
              :aria-invalid="fieldErrors.reason ? 'true' : 'false'"
              data-test="reason"
            />
            <p v-if="fieldErrors.reason" class="field-error" role="alert" data-test="reason-error">
              {{ msg(fieldErrors.reason) }}
            </p>
          </div>
          <div class="btn-row">
            <button
              type="button"
              :class="['btn', mode === 'approve' ? 'btn-primary' : 'btn-danger']"
              data-test="confirm"
              :disabled="busyId === row.id"
              :aria-busy="busyId === row.id"
              @click="confirm(row)"
            >
              {{
                mode === 'approve'
                  ? t('admin.orders.confirmApprove')
                  : t('admin.orders.confirmReject')
              }}
            </button>
            <button type="button" class="btn" data-test="cancel" @click="close">
              {{ t('common.cancel') }}
            </button>
          </div>
        </div>
        <div v-else class="btn-row">
          <button
            type="button"
            class="btn btn-primary"
            data-test="approve"
            @click="open(row.id, 'approve')"
          >
            {{ t('admin.orders.approve') }}
          </button>
          <button
            type="button"
            class="btn btn-danger"
            data-test="reject"
            @click="open(row.id, 'reject')"
          >
            {{ t('admin.orders.reject') }}
          </button>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.review-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.review-row {
  display: grid;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.details {
  display: grid;
  gap: 0.5rem;
  margin: 0;
}
.details div {
  display: grid;
  gap: 0.125rem;
}
dt {
  font-weight: 600;
}
dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.lines {
  margin: 0;
  padding-inline-start: 1.25rem;
}
.panel {
  display: grid;
  gap: 0.75rem;
}
.field {
  display: grid;
  gap: 0.375rem;
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
input[aria-invalid='true'] {
  border-color: #b42318;
}
.hint,
.field-error {
  margin: 0;
  font-size: 0.875rem;
}
.hint {
  color: #52606d;
}
.field-error {
  color: #b42318;
}
</style>
