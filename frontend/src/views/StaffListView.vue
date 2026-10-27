<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as staffApi from '@/api/staff'
import { formMessage } from '@/utils/forms'

// Drivers, traders or clients for Admin and Manager (BL-056, BL-057, BL-058): one list, three kinds.
const props = defineProps({
  kind: {
    type: String,
    required: true,
    validator: (v) => ['drivers', 'traders', 'clients'].includes(v),
  },
})
const { t } = useI18n()
const STATUSES = ['pending_approval', 'active', 'deactivated', 'rejected']

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const search = ref('')
const status = ref('')
const page = ref(1)
const next = ref(null)
const previous = ref(null)

const query = computed(() => ({
  page: page.value,
  status: status.value,
  search: search.value.trim(),
}))

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    const data = await staffApi.listStaff(props.kind, query.value)
    rows.value = data.results
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

let timer = null
watch([search, status], () => {
  page.value = 1
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})
// The same component serves the three routes, so a route change starts fresh.
watch(
  () => props.kind,
  () => {
    search.value = ''
    status.value = ''
    page.value = 1
    load()
  },
)

function go(delta) {
  page.value += delta
  load()
}

// Count column per kind: delivered orders for drivers, orders for the others.
const countOf = (row) => (props.kind === 'drivers' ? row.delivered_orders : row.orders)
</script>

<template>
  <section>
    <h1>{{ t(`admin.staff.${kind}.title`) }}</h1>

    <p v-if="kind === 'drivers'">
      <RouterLink to="/admin/drivers/performance" class="touch-link" data-test="performance">{{
        t('admin.performance.title')
      }}</RouterLink>
    </p>

    <form class="filters" role="search" @submit.prevent="load">
      <label>
        {{ t('admin.users.search') }}
        <input v-model="search" type="search" name="search" data-test="search" />
      </label>
      <label>
        {{ t('admin.users.status') }}
        <select v-model="status" data-test="status-filter">
          <option value="">{{ t('admin.users.all') }}</option>
          <option v-for="s in STATUSES" :key="s" :value="s">{{ t(`statuses.${s}`) }}</option>
        </select>
      </label>
    </form>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t(`admin.staff.${kind}.empty`)"
      @retry="load"
    />

    <div v-if="!loading && !loadError && rows.length" class="scroll">
      <table class="staff">
        <caption class="sr-only">
          {{
            t(`admin.staff.${kind}.title`)
          }}
        </caption>
        <thead>
          <tr>
            <th scope="col">{{ t('places.name') }}</th>
            <th scope="col">{{ t('admin.staff.phone') }}</th>
            <th v-if="kind === 'traders'" scope="col">{{ t('admin.staff.shop') }}</th>
            <th scope="col">{{ t('admin.users.status') }}</th>
            <th scope="col">{{ t(`admin.staff.${kind}.count`) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" data-test="row">
            <td>
              <RouterLink :to="`/admin/${kind}/${row.id}`" data-test="open">{{
                row.full_name
              }}</RouterLink>
            </td>
            <td dir="ltr">{{ row.phone }}</td>
            <td v-if="kind === 'traders'" data-test="shop">{{ row.shop_name || '—' }}</td>
            <td data-test="status">{{ t(`statuses.${row.status}`) }}</td>
            <td data-test="count">{{ countOf(row) }}</td>
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
.staff {
  inline-size: 100%;
  border-collapse: collapse;
}
th,
td {
  padding: 0.5rem;
  text-align: start;
  border-block-end: 1px solid var(--color-border);
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
