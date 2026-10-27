<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ListStatus from '@/components/ListStatus.vue'
import * as ordersApi from '@/api/orders'
import { formMessage } from '@/utils/forms'

// The driver's own performance (BL-063): aggregates only, per month or all-time.
const { t } = useI18n()

const data = ref(null)
const month = ref('')
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
// The month list comes from the first (all-time) answer so it stays stable while picking.
const months = ref([])

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    data.value = await ordersApi.getMyPerformance(month.value)
    if (!month.value) months.value = data.value.months
  } catch (err) {
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    loading.value = false
  }
}
onMounted(load)

const hasHistory = () => months.value.length > 0
const average = (d) =>
  d.average_rating === null ? t('performance.noRatings') : `${d.average_rating} / 5`
</script>

<template>
  <section class="form-page">
    <h1>{{ t('performance.title') }}</h1>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />

    <template v-if="data && !loading">
      <p v-if="!hasHistory()" class="empty-state" data-test="empty">{{ t('performance.empty') }}</p>

      <label v-if="hasHistory()" class="picker">
        {{ t('performance.month') }}
        <select v-model="month" data-test="month" @change="load">
          <option value="">{{ t('performance.allTime') }}</option>
          <option v-for="m in months" :key="m.month" :value="m.month">{{ m.month }}</option>
        </select>
      </label>

      <ul class="cards">
        <li class="card" data-test="delivered">
          <span class="count">{{ data.delivered }}</span>
          <span>{{ t('performance.delivered') }}</span>
        </li>
        <li class="card" data-test="cancelled">
          <span class="count">{{ data.cancelled }}</span>
          <span>{{ t('performance.cancelled') }}</span>
        </li>
        <li class="card" data-test="rating">
          <span class="count">{{ average(data) }}</span>
          <span>{{ t('performance.rating', { n: data.rating_count }) }}</span>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.picker {
  display: grid;
  gap: 0.25rem;
  font-weight: 600;
  margin-block-end: 1rem;
}
select {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.5rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.card {
  display: grid;
  gap: 0.25rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.count {
  font-size: 1.5rem;
  font-weight: 700;
}
</style>
