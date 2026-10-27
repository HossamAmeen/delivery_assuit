<script setup>
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as ordersApi from '@/api/orders'
import { formMessage } from '@/utils/forms'

// Basic overview of every driver's performance for Admin and Manager (BL-060).
const { t } = useI18n()

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const ordering = ref('delivered')
const month = ref('')
const page = ref(1)
const next = ref(null)
const previous = ref(null)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    const data = await ordersApi.listDriverPerformance({
      month: month.value,
      ordering: ordering.value,
      page: page.value,
    })
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
watch([ordering, month], () => {
  page.value = 1
  load()
})
function go(delta) {
  page.value += delta
  load()
}
const average = (r) => (r.average_rating === null ? '—' : r.average_rating)
</script>

<template>
  <section>
    <h1>{{ t('admin.performance.title') }}</h1>

    <div class="filters">
      <label>
        {{ t('admin.performance.sort') }}
        <select v-model="ordering" data-test="ordering">
          <option value="delivered">{{ t('admin.performance.byDelivered') }}</option>
          <option value="rating">{{ t('admin.performance.byRating') }}</option>
        </select>
      </label>
      <label>
        {{ t('performance.month') }}
        <input v-model="month" type="month" name="month" data-test="month" />
      </label>
    </div>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('admin.performance.empty')"
      @retry="load"
    />

    <div v-if="!loading && !loadError && rows.length" class="scroll">
      <table class="perf">
        <caption class="sr-only">
          {{
            t('admin.performance.title')
          }}
        </caption>
        <thead>
          <tr>
            <th scope="col">{{ t('places.name') }}</th>
            <th scope="col">{{ t('performance.delivered') }}</th>
            <th scope="col">{{ t('performance.cancelled') }}</th>
            <th scope="col">{{ t('admin.performance.average') }}</th>
            <th scope="col">{{ t('admin.performance.ratings') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id" data-test="row">
            <td>
              <RouterLink :to="`/admin/drivers/${r.id}`" data-test="open">{{
                r.full_name
              }}</RouterLink>
            </td>
            <td data-test="delivered">{{ r.delivered }}</td>
            <td data-test="cancelled">{{ r.cancelled }}</td>
            <td data-test="average">{{ average(r) }}</td>
            <td data-test="count">{{ r.rating_count }}</td>
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
.perf {
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
