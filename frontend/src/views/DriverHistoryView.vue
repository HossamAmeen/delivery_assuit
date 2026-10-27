<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as ordersApi from '@/api/orders'
import { formMessage } from '@/utils/forms'
import { formatDateTime } from '@/utils/format'

// My Orders (BL-034): delivered and cancelled orders, newest first, paginated.
const { t, locale } = useI18n()

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const page = ref(1)
const next = ref(null)
const previous = ref(null)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    const data = await ordersApi.listOrders({ scope: 'history', page: page.value })
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

function go(delta) {
  page.value += delta
  load()
}

// The date that matters: when it was delivered, or when it was cancelled.
const finishedAt = (o) =>
  formatDateTime(o.delivered_at || o.cancelled_at || o.modified_at, locale.value)
</script>

<template>
  <section>
    <h1>{{ t('orders.historyTitle') }}</h1>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('orders.historyEmpty')"
      @retry="load"
    />

    <ul v-if="!loading && !loadError && rows.length" class="history">
      <li v-for="order in rows" :key="order.id" class="row" data-test="row">
        <div>
          <strong dir="ltr" data-test="reference">{{ order.reference }}</strong>
          <span class="role-badge" data-test="status">{{
            t(`orders.status.${order.status}`)
          }}</span>
          <p class="when" data-test="when">{{ finishedAt(order) }}</p>
        </div>
        <RouterLink :to="`/driver/orders/${order.id}`" class="btn touch-link" data-test="open">{{
          t('orders.details')
        }}</RouterLink>
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
.history {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.when {
  margin: 0.25rem 0 0;
}
.btn {
  text-decoration: none;
}
.pager {
  display: flex;
  gap: 0.5rem;
  margin-block-start: 1rem;
}
</style>
