<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as ordersApi from '@/api/orders'
import { formMessage } from '@/utils/forms'
import { formatDateTime } from '@/utils/format'

// All orders for Admin and Manager (BL-054).
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

const rows = ref([])
const count = ref(0)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const status = ref('')
const from = ref('')
const to = ref('')
const search = ref('')
const page = ref(1)
const next = ref(null)
const previous = ref(null)

const query = computed(() => ({
  page: page.value,
  status: status.value,
  created_from: from.value,
  created_to: to.value,
  search: search.value.trim(),
}))

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    const data = await ordersApi.listOrders(query.value)
    rows.value = data.results
    count.value = data.count
    next.value = data.next
    previous.value = data.previous
  } catch (err) {
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    loading.value = false
  }
}
onMounted(load)

// A new filter starts again at page 1.
let timer = null
watch([status, from, to, search], () => {
  page.value = 1
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})

function go(delta) {
  page.value += delta
  load()
}

const place = (p) => p.name
</script>

<template>
  <section>
    <h1>{{ t('admin.table.title') }}</h1>

    <form class="filters" role="search" @submit.prevent="load">
      <label>
        {{ t('admin.table.search') }}
        <input v-model="search" type="search" name="search" dir="ltr" data-test="search" />
      </label>
      <label>
        {{ t('admin.users.status') }}
        <select v-model="status" data-test="status-filter">
          <option value="">{{ t('admin.users.all') }}</option>
          <option v-for="s in STATUSES" :key="s" :value="s">{{ t(`orders.status.${s}`) }}</option>
        </select>
      </label>
      <label>
        {{ t('admin.table.from') }}
        <input v-model="from" type="date" name="from" data-test="from" />
      </label>
      <label>
        {{ t('admin.table.to') }}
        <input v-model="to" type="date" name="to" data-test="to" />
      </label>
    </form>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('admin.table.empty')"
      @retry="load"
    />

    <div v-if="!loading && !loadError && rows.length" class="scroll">
      <table class="orders">
        <caption class="sr-only">
          {{
            t('admin.table.title')
          }}
        </caption>
        <thead>
          <tr>
            <th scope="col">{{ t('admin.table.reference') }}</th>
            <th scope="col">{{ t('admin.orders.client') }}</th>
            <th scope="col">{{ t('orders.shop') }}</th>
            <th scope="col">{{ t('admin.table.driver') }}</th>
            <th scope="col">{{ t('admin.orders.pickup') }}</th>
            <th scope="col">{{ t('admin.orders.delivery') }}</th>
            <th scope="col">{{ t('admin.users.status') }}</th>
            <th scope="col">{{ t('admin.table.fee') }}</th>
            <th scope="col">{{ t('admin.table.created') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in rows" :key="o.id" data-test="row">
            <td>
              <RouterLink :to="`/admin/orders/${o.id}`" dir="ltr" data-test="open">{{
                o.reference
              }}</RouterLink>
            </td>
            <td data-test="client">{{ o.client.full_name }}</td>
            <td data-test="shop">{{ o.shop ? o.shop.name : '—' }}</td>
            <td data-test="driver">{{ o.driver ? o.driver.full_name : '—' }}</td>
            <td>{{ place(o.pickup) }}</td>
            <td>{{ place(o.delivery) }}</td>
            <td data-test="status">{{ t(`orders.status.${o.status}`) }}</td>
            <td data-test="fee">{{ o.delivery_fee === null ? '—' : o.delivery_fee }}</td>
            <td>{{ formatDateTime(o.created_at, locale) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

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
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-block-end: 1rem;
}
label {
  display: grid;
  gap: 0.25rem;
  font-weight: 600;
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
.scroll {
  overflow-x: auto;
}
.orders {
  inline-size: 100%;
  border-collapse: collapse;
}
th,
td {
  padding: 0.5rem;
  text-align: start;
  border-block-end: 1px solid var(--color-border);
  white-space: nowrap;
}
.sr-only {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}
.pager {
  display: flex;
  gap: 0.5rem;
  margin-block-start: 1rem;
}
</style>
