<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import NextActionButton from '@/components/NextActionButton.vue'
import * as ordersApi from '@/api/orders'
import { ApiError } from '@/api/http'
import { formMessage } from '@/utils/forms'
import { formatDateTime } from '@/utils/format'

// A driver's order (BL-030, BL-032). Contact phones arrive only while the job is active (BR-16).
const { t, locale } = useI18n()
const route = useRoute()
const id = computed(() => route.params.id)

const order = ref(null)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const missing = ref(false)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  missing.value = false
  try {
    order.value = await ordersApi.getOrder(id.value)
  } catch (err) {
    // Not assigned to this driver (or no longer visible) is a 404.
    if (err instanceof ApiError && err.status === 404) missing.value = true
    else {
      offline.value = Boolean(err?.isNetworkError)
      loadError.value = formMessage(err, t)
    }
  } finally {
    loading.value = false
  }
}
onMounted(load)

const updated = (next) => (next ? (order.value = next) : load())
const place = (p) => `${p.name} — ${p.address}`
const tel = (phone) => `tel:${phone}`
</script>

<template>
  <section class="form-page">
    <p>
      <RouterLink to="/driver" class="touch-link">{{ t('orders.backHome') }}</RouterLink>
    </p>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />
    <div v-if="missing" class="form-notice" role="status" data-test="missing">
      {{ t('orders.notFound') }}
    </div>

    <template v-if="order && !loading">
      <h1 dir="ltr" data-test="reference">{{ order.reference }}</h1>
      <p>
        <span class="role-badge" data-test="status">{{ t(`orders.status.${order.status}`) }}</span>
      </p>

      <NextActionButton :order="order" @updated="updated" />

      <dl class="details">
        <div>
          <dt>{{ t('admin.orders.pickup') }}</dt>
          <dd data-test="pickup">{{ place(order.pickup) }}</dd>
        </div>
        <div>
          <dt>{{ t('admin.orders.delivery') }}</dt>
          <dd data-test="delivery">{{ place(order.delivery) }}</dd>
        </div>
        <div v-if="order.description">
          <dt>{{ t('admin.orders.description') }}</dt>
          <dd data-test="description">{{ order.description }}</dd>
        </div>
        <div v-if="order.items.length">
          <dt>{{ t('admin.orders.items') }}</dt>
          <dd>
            <ul class="lines">
              <li v-for="(line, i) in order.items" :key="i" data-test="line">
                {{ line.quantity }} × {{ line.name }}
              </li>
            </ul>
          </dd>
        </div>
        <div v-if="order.shop">
          <dt>{{ t('orders.shop') }}</dt>
          <dd>
            <span data-test="shop-name">{{ order.shop.name }}</span>
            <a
              v-if="order.shop.phone"
              :href="tel(order.shop.phone)"
              dir="ltr"
              data-test="shop-phone"
              >{{ order.shop.phone }}</a
            >
          </dd>
        </div>
        <div>
          <dt>{{ t('admin.orders.client') }}</dt>
          <dd>
            <span data-test="client-name">{{ order.client.full_name }}</span>
            <a
              v-if="order.client.phone"
              :href="tel(order.client.phone)"
              dir="ltr"
              data-test="client-phone"
              >{{ order.client.phone }}</a
            >
          </dd>
        </div>
        <div v-if="order.assigned_at">
          <dt>{{ t('orders.assignedAt') }}</dt>
          <dd data-test="assigned-at">{{ formatDateTime(order.assigned_at, locale) }}</dd>
        </div>
        <div v-if="order.delivered_at">
          <dt>{{ t('orders.deliveredAt') }}</dt>
          <dd data-test="delivered-at">{{ formatDateTime(order.delivered_at, locale) }}</dd>
        </div>
        <div v-if="order.status === 'cancelled' && order.cancel_reason">
          <dt>{{ t('orders.cancelReason') }}</dt>
          <dd data-test="cancel-reason">{{ order.cancel_reason }}</dd>
        </div>
      </dl>
    </template>
  </section>
</template>

<style scoped>
.details {
  display: grid;
  gap: 0.75rem;
  margin: 1rem 0 0;
}
.details div {
  display: grid;
  gap: 0.125rem;
}
dt {
  font-weight: 600;
}
dd {
  display: grid;
  gap: 0.25rem;
  margin: 0;
  overflow-wrap: anywhere;
}
.lines {
  margin: 0;
  padding-inline-start: 1.25rem;
}
</style>
