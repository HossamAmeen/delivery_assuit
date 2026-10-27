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
const drivers = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const busyId = ref(null)
const actionError = ref('')
const doneNotice = ref('')
// order id -> chosen driver id (as the select's string value), and its field error
const chosen = ref({})
const errors = ref({})

async function loadDrivers() {
  drivers.value = (await ordersApi.listDrivers({ page_size: 100 })).results
}

// `silent` refreshes quietly (auto-refresh): no spinner, errors are ignored so the screen stays.
async function load({ silent = false } = {}) {
  if (!silent) loading.value = true
  if (!silent) loadError.value = ''
  if (!silent) offline.value = false
  try {
    const [orders] = await Promise.all([
      ordersApi.listOrders({ status: 'available', page_size: 100 }),
      loadDrivers(),
    ])
    rows.value = orders.results
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

const place = (p) => `${p.name} — ${p.address}`

async function assign(row) {
  if (busyId.value) return
  actionError.value = ''
  doneNotice.value = ''
  const driverId = chosen.value[row.id]
  if (!driverId) {
    errors.value = { ...errors.value, [row.id]: clientError('admin.assign.errors.driverRequired') }
    return
  }
  errors.value = { ...errors.value, [row.id]: '' }
  busyId.value = row.id
  try {
    const updated = await ordersApi.assignOrder(row.id, Number(driverId))
    rows.value = rows.value.filter((r) => r.id !== row.id)
    doneNotice.value = t('admin.assign.done', {
      reference: row.reference,
      driver: updated.driver?.full_name ?? '',
    })
    // The chosen driver is busy now, so the picker must reflect it.
    await loadDrivers().catch(() => {})
  } catch (err) {
    const fields = serverFieldErrors(err, ['driver', 'status'])
    if (fields.driver) {
      errors.value = { ...errors.value, [row.id]: fields.driver }
      await loadDrivers().catch(() => {})
    } else {
      actionError.value = fields.status || formMessage(err, t)
      // Someone else already assigned or cancelled it: the row is stale.
      if (err?.status === 400) await load()
    }
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <section>
    <h1>{{ t('admin.assign.title') }}</h1>
    <p v-if="doneNotice" class="form-notice" role="status" data-test="done">{{ doneNotice }}</p>
    <p v-if="actionError" class="form-error" role="alert" data-test="action-error">
      {{ actionError }}
    </p>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('admin.assign.empty')"
      @retry="load"
    />

    <p
      v-if="!loading && !loadError && rows.length && drivers.length === 0"
      class="form-notice"
      data-test="no-drivers"
    >
      {{ t('admin.assign.noDrivers') }}
    </p>

    <ul v-if="!loading && !loadError && rows.length" class="assign-list">
      <li v-for="row in rows" :key="row.id" class="assign-row" data-test="row">
        <div class="head">
          <strong dir="ltr" data-test="reference">{{ row.reference }}</strong>
          <span class="role-badge">{{ row.shop ? row.shop.name : t('admin.orders.direct') }}</span>
        </div>
        <p class="line">{{ t('admin.orders.pickup') }}: {{ place(row.pickup) }}</p>
        <p class="line">{{ t('admin.orders.delivery') }}: {{ place(row.delivery) }}</p>
        <p v-if="row.delivery_fee !== null" class="line" data-test="fee">
          {{ t('admin.orders.fee') }}: {{ row.delivery_fee }}
        </p>

        <div class="field">
          <label :for="`driver-${row.id}`">{{ t('admin.assign.driver') }}</label>
          <select
            :id="`driver-${row.id}`"
            v-model="chosen[row.id]"
            :disabled="busyId === row.id"
            :aria-invalid="errors[row.id] ? 'true' : 'false'"
            data-test="driver"
          >
            <option value="">{{ t('places.choose') }}</option>
            <option
              v-for="d in drivers"
              :key="d.id"
              :value="String(d.id)"
              :disabled="d.has_active_order"
            >
              {{ d.full_name
              }}{{
                d.has_active_order
                  ? ` — ${t('admin.assign.busy', { reference: d.active_order_reference })}`
                  : ''
              }}
            </option>
          </select>
          <p v-if="errors[row.id]" class="field-error" role="alert" data-test="driver-error">
            {{ msg(errors[row.id]) }}
          </p>
        </div>
        <div class="btn-row">
          <button
            type="button"
            class="btn btn-primary"
            data-test="assign"
            :disabled="busyId === row.id"
            :aria-busy="busyId === row.id"
            @click="assign(row)"
          >
            {{ busyId === row.id ? t('admin.assign.assigning') : t('admin.assign.assign') }}
          </button>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.assign-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.assign-row {
  display: grid;
  gap: 0.5rem;
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
.line {
  margin: 0;
  overflow-wrap: anywhere;
}
.field {
  display: grid;
  gap: 0.375rem;
}
label {
  font-weight: 600;
}
select {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.5rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
}
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
</style>
