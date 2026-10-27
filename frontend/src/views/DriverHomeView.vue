<script setup>
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import NextActionButton from '@/components/NextActionButton.vue'
import * as ordersApi from '@/api/orders'
import { useAuthStore } from '@/stores/auth'
import { formMessage } from '@/utils/forms'
import { formatDateTime } from '@/utils/format'

// Driver home (BL-029, BL-033): the active order, prominent, with its next action.
const { t, locale } = useI18n()
const auth = useAuthStore()

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)

// `silent` refreshes quietly (auto-refresh): no spinner, errors are ignored so the screen stays.
async function load({ silent = false } = {}) {
  if (!silent) loading.value = true
  if (!silent) loadError.value = ''
  if (!silent) offline.value = false
  try {
    rows.value = (await ordersApi.listOrders({ scope: 'active', page_size: 50 })).results
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

// After a step: swap the order in place; if it left the active set (delivered), drop it.
function updated(order, next) {
  if (!next) return load()
  rows.value = next.next_action
    ? rows.value.map((r) => (r.id === order.id ? next : r))
    : rows.value.filter((r) => r.id !== order.id)
}

const place = (p) => `${p.name} — ${p.address}`
</script>

<template>
  <article class="role-home" data-testid="home-driver">
    <h1>{{ t('home.driver') }}</h1>
    <p class="role-home-user">
      <strong data-testid="home-name">{{ auth.user?.full_name }}</strong>
      <span class="role-badge" data-testid="home-role">{{ t('roles.driver') }}</span>
    </p>

    <p>
      <button type="button" class="btn" data-test="refresh" :disabled="loading" @click="load">
        {{ t('orders.refresh') }}
      </button>
    </p>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />

    <p
      v-if="!loading && !loadError && rows.length === 0"
      class="empty-state"
      data-testid="home-empty"
    >
      {{ t('orders.noAssigned') }}
    </p>

    <ul v-if="!loading && !loadError && rows.length" class="active-list">
      <li v-for="(order, i) in rows" :key="order.id" class="active-card" data-test="order">
        <div class="head">
          <strong dir="ltr" data-test="reference">{{ order.reference }}</strong>
          <span class="role-badge" data-test="status">{{
            t(`orders.status.${order.status}`)
          }}</span>
        </div>
        <p v-if="i === 0 && rows.length > 1" class="note">{{ t('orders.newest') }}</p>
        <p class="line">{{ t('admin.orders.pickup') }}: {{ place(order.pickup) }}</p>
        <p class="line">{{ t('admin.orders.delivery') }}: {{ place(order.delivery) }}</p>
        <p v-if="order.description" class="line" data-test="description">{{ order.description }}</p>
        <p v-if="order.assigned_at" class="line" data-test="assigned-at">
          {{ t('orders.assignedAt') }}: {{ formatDateTime(order.assigned_at, locale) }}
        </p>
        <NextActionButton :order="order" @updated="updated(order, $event)" />
        <RouterLink :to="`/driver/orders/${order.id}`" class="btn touch-link" data-test="open">{{
          t('orders.details')
        }}</RouterLink>
      </li>
    </ul>
  </article>
</template>

<style scoped>
.active-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.active-card {
  display: grid;
  gap: 0.5rem;
  padding: 1rem;
  border: 2px solid var(--color-primary);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.line,
.note {
  margin: 0;
  overflow-wrap: anywhere;
}
.btn {
  text-decoration: none;
}
</style>
