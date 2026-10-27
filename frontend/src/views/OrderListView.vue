<script setup>
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as ordersApi from '@/api/orders'
import { formMessage } from '@/utils/forms'
import { formatDateTime } from '@/utils/format'

// A client's or a trader's own orders (BL-038, BL-049), newest first, filterable by status.
// `base` says which area the detail links go to.
const props = defineProps({
  base: { type: String, required: true, validator: (v) => ['client', 'trader'].includes(v) },
})
const { t, locale } = useI18n()
const STATUSES = [
  'created',
  'available',
  'assigned',
  'picked_up',
  'in_delivery',
  'delivered',
  'cancelled',
]
const FINISHED = ['delivered', 'cancelled']
// A trader never sees unreviewed orders, so that choice would always be empty.
const statuses = computed(() => (props.base === 'trader' ? STATUSES.slice(1) : STATUSES))

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const status = ref('')
const search = ref('')
const page = ref(1)
const next = ref(null)
const previous = ref(null)

// `silent` refreshes quietly (auto-refresh): no spinner, errors are ignored so the screen stays.
async function load({ silent = false } = {}) {
  if (!silent) loading.value = true
  if (!silent) loadError.value = ''
  if (!silent) offline.value = false
  try {
    const data = await ordersApi.listOrders({
      page: page.value,
      status: status.value,
      search: search.value.trim(),
    })
    rows.value = data.results
    next.value = data.next
    previous.value = data.previous
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
// Search by reference waits a moment after typing; a new filter starts again at page 1.
let timer = null
watch([status, search], () => {
  page.value = 1
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})
function go(delta) {
  page.value += delta
  load()
}
const isActive = (o) => !FINISHED.includes(o.status)
</script>

<template>
  <section>
    <h1>{{ t(`orders.list.${base}`) }}</h1>

    <label class="filter">
      {{ t('admin.table.search') }}
      <input v-model="search" type="search" name="search" dir="ltr" data-test="search" />
    </label>
    <label class="filter">
      {{ t('admin.users.status') }}
      <select v-model="status" data-test="status-filter">
        <option value="">{{ t('admin.users.all') }}</option>
        <option v-for="s in statuses" :key="s" :value="s">{{ t(`orders.status.${s}`) }}</option>
      </select>
    </label>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('orders.list.empty')"
      @retry="load"
    />

    <ul v-if="!loading && !loadError && rows.length" class="orders">
      <li v-for="o in rows" :key="o.id" :class="['row', { active: isActive(o) }]" data-test="row">
        <div>
          <RouterLink :to="`/${base}/orders/${o.id}`" dir="ltr" data-test="open">{{
            o.reference
          }}</RouterLink>
          <span class="role-badge" data-test="status">{{ t(`orders.status.${o.status}`) }}</span>
          <span v-if="isActive(o)" class="role-badge" data-test="active">{{
            t('orders.list.active')
          }}</span>
          <p class="line">{{ o.pickup.name }} → {{ o.delivery.name }}</p>
          <p class="line" data-test="date">{{ formatDateTime(o.created_at, locale) }}</p>
        </div>
      </li>
    </ul>

    <nav v-if="previous || next" class="pager" :aria-label="t('admin.users.pager')">
      <button type="button" class="btn" data-test="prev" :disabled="!previous" @click="go(-1)">
        {{ t('admin.users.previous') }}
      </button>
      <button type="button" class="btn" data-test="next" :disabled="!next" @click="go(1)">
        {{ t('admin.users.next') }}
      </button>
    </nav>
  </section>
</template>

<style scoped>
.filter {
  display: grid;
  gap: 0.25rem;
  font-weight: 600;
  margin-block-end: 1rem;
}
input,
select {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.5rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
}
.orders {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.row {
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.row.active {
  border-inline-start: 4px solid var(--color-primary);
}
.line {
  margin: 0.25rem 0 0;
}
.pager {
  display: flex;
  gap: 0.5rem;
  margin-block-start: 1rem;
}
</style>
