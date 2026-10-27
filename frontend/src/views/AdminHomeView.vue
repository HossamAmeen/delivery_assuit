<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as ordersApi from '@/api/orders'
import { useAuthStore } from '@/stores/auth'
import { formMessage } from '@/utils/forms'

// Admin and Manager dashboard (BL-053): account cards and order counts for a chosen period.
const { t } = useI18n()
const auth = useAuthStore()

const PERIODS = ['', 'today', 'week', 'month', 'custom']
const period = ref('')
const from = ref('')
const to = ref('')
const data = ref(null)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const rangeError = ref(false)

const params = computed(() => ({ period: period.value, from: from.value, to: to.value }))

async function load() {
  rangeError.value = false
  if (period.value === 'custom' && (!from.value || !to.value || from.value > to.value)) {
    // Wait for a complete, sensible range instead of asking the server for a 400.
    rangeError.value = Boolean(from.value && to.value)
    return
  }
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    data.value = await ordersApi.getDashboard(params.value)
  } catch (err) {
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch([period, from, to], load)

const ACCOUNT_ROWS = ['active', 'inactive', 'pending']
</script>

<template>
  <article class="role-home" data-testid="home-admin">
    <h1>{{ t('home.admin') }}</h1>
    <p class="role-home-user">
      <strong data-testid="home-name">{{ auth.user?.full_name }}</strong>
      <span class="role-badge" data-testid="home-role">{{ t(`roles.${auth.role}`) }}</span>
    </p>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />

    <template v-if="data">
      <p
        v-if="data.orders.total === 0 && data.drivers.total === 0"
        class="empty-state"
        data-testid="home-empty"
      >
        {{ t('admin.dashboard.empty') }}
      </p>

      <div class="cards">
        <section class="card" data-test="drivers">
          <h2>{{ t('admin.nav.drivers') }}</h2>
          <p class="count" data-test="total">{{ data.drivers.total }}</p>
          <ul>
            <li v-for="k in ACCOUNT_ROWS" :key="k" :data-test="k">
              {{ t(`admin.dashboard.${k}`) }}: {{ data.drivers[k] }}
            </li>
          </ul>
          <RouterLink to="/admin/drivers" class="touch-link">{{
            t('admin.nav.drivers')
          }}</RouterLink>
        </section>

        <section class="card" data-test="traders">
          <h2>{{ t('admin.nav.traders') }}</h2>
          <p class="count" data-test="total">{{ data.traders.total }}</p>
          <ul>
            <li v-for="k in ACCOUNT_ROWS" :key="k" :data-test="k">
              {{ t(`admin.dashboard.${k}`) }}: {{ data.traders[k] }}
            </li>
          </ul>
          <RouterLink to="/admin/traders" class="touch-link">{{
            t('admin.nav.traders')
          }}</RouterLink>
        </section>

        <section class="card" data-test="clients">
          <h2>{{ t('admin.nav.clients') }}</h2>
          <p class="count" data-test="total">{{ data.clients.total }}</p>
          <RouterLink to="/admin/clients" class="touch-link">{{
            t('admin.nav.clients')
          }}</RouterLink>
        </section>
      </div>

      <h2>{{ t('admin.dashboard.ordersTitle') }}</h2>
      <div class="filters">
        <label>
          {{ t('admin.dashboard.period') }}
          <select v-model="period" data-test="period">
            <option v-for="p in PERIODS" :key="p" :value="p">
              {{ t(`admin.dashboard.periods.${p || 'all'}`) }}
            </option>
          </select>
        </label>
        <template v-if="period === 'custom'">
          <label>
            {{ t('admin.table.from') }}
            <input v-model="from" type="date" data-test="from" />
          </label>
          <label>
            {{ t('admin.table.to') }}
            <input v-model="to" type="date" data-test="to" />
          </label>
        </template>
      </div>
      <p v-if="rangeError" class="form-error" role="alert" data-test="range-error">
        {{ t('admin.dashboard.rangeError') }}
      </p>

      <div class="cards" data-test="orders">
        <section class="card" data-test="orders-total">
          <p class="count">{{ data.orders.total }}</p>
          <p>{{ t('admin.dashboard.total') }}</p>
        </section>
        <section class="card" data-test="orders-pending">
          <p class="count">{{ data.orders.pending }}</p>
          <p>{{ t('admin.dashboard.pending') }}</p>
        </section>
        <section class="card" data-test="orders-in_progress">
          <p class="count">{{ data.orders.in_progress }}</p>
          <p>{{ t('admin.dashboard.inProgress') }}</p>
        </section>
        <section class="card" data-test="orders-delivered">
          <p class="count">{{ data.orders.delivered }}</p>
          <p>{{ t('admin.dashboard.delivered') }}</p>
        </section>
        <section class="card" data-test="orders-cancelled">
          <p class="count">{{ data.orders.cancelled }}</p>
          <p>{{ t('admin.dashboard.cancelled') }}</p>
        </section>
      </div>
      <p class="hint" data-test="help">{{ t('admin.dashboard.help') }}</p>
    </template>
  </article>
</template>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: 0.75rem;
}
.card {
  display: grid;
  gap: 0.25rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.card h2 {
  margin: 0;
  font-size: 1rem;
}
.card ul {
  margin: 0;
  padding-inline-start: 1rem;
}
.card p {
  margin: 0;
}
.count {
  font-size: 1.5rem;
  font-weight: 700;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-block-end: 0.75rem;
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
.hint {
  color: #52606d;
  font-size: 0.875rem;
}
</style>
