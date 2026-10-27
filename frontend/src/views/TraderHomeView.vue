<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as ordersApi from '@/api/orders'
import { useAuthStore } from '@/stores/auth'
import { formMessage } from '@/utils/forms'

// Trader dashboard (BL-040): counts of the shop's orders. The same numbers as the order list.
const { t } = useI18n()
const auth = useAuthStore()

const summary = ref(null)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    summary.value = await ordersApi.getSummary()
  } catch (err) {
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    loading.value = false
  }
}
onMounted(load)

const CARDS = [
  ['total', 'total'],
  ['waiting_for_driver', 'waiting'],
  ['in_progress', 'progress'],
  ['delivered', 'delivered'],
  ['cancelled', 'cancelled'],
]
</script>

<template>
  <article class="role-home" data-testid="home-trader">
    <h1>{{ t('home.trader') }}</h1>
    <p class="role-home-user">
      <strong data-testid="home-name">{{ auth.user?.full_name }}</strong>
      <span class="role-badge" data-testid="home-role">{{ t('roles.trader') }}</span>
    </p>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />

    <template v-if="summary && !loading">
      <p v-if="summary.total === 0" class="empty-state" data-testid="home-empty">
        {{ t('trader.dashboard.empty') }}
      </p>
      <ul class="cards">
        <li v-for="[key, label] in CARDS" :key="key" class="card" :data-test="`card-${key}`">
          <span class="count" data-test="count">{{ summary[key] }}</span>
          <span>{{ t(`trader.dashboard.${label}`) }}</span>
        </li>
      </ul>
      <p>
        <RouterLink to="/trader/orders" class="btn touch-link" data-test="see-orders">{{
          t('trader.dashboard.seeOrders')
        }}</RouterLink>
      </p>
    </template>
  </article>
</template>

<style scoped>
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
.btn {
  text-decoration: none;
}
</style>
