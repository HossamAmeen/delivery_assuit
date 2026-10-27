<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import OrderTimeline from '@/components/OrderTimeline.vue'

// A read-only order for a client or a trader (BL-038, BL-039, BL-050): status, driver name,
// places, items, fee and the timeline. No phone numbers are shown (BR-16).
const props = defineProps({ order: { type: Object, required: true } })
const { t } = useI18n()

const place = (p) => `${p.name} — ${p.address}`
const driverText = computed(() => {
  if (props.order.driver) return props.order.driver.full_name
  if (props.order.status === 'cancelled') return ''
  return t('orders.waitingDriver')
})
</script>

<template>
  <div>
    <p>
      <span class="role-badge" data-test="status">{{ t(`orders.status.${order.status}`) }}</span>
    </p>
    <dl class="details">
      <div v-if="driverText">
        <dt>{{ t('admin.table.driver') }}</dt>
        <dd data-test="driver">{{ driverText }}</dd>
      </div>
      <div v-if="order.shop">
        <dt>{{ t('orders.shop') }}</dt>
        <dd data-test="shop">{{ order.shop.name }}</dd>
      </div>
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
              <span v-if="line.price !== null" data-test="line-price">({{ line.price }})</span>
            </li>
          </ul>
          <span v-if="order.items_total !== null" data-test="items-total"
            >{{ t('staffOrder.itemsTotal') }}: {{ order.items_total }}</span
          >
        </dd>
      </div>
      <div v-if="order.delivery_fee !== null">
        <dt>{{ t('admin.table.fee') }}</dt>
        <dd data-test="fee">{{ order.delivery_fee }}</dd>
      </div>
      <div v-if="order.status === 'cancelled' && order.cancel_reason">
        <dt>{{ t('orders.cancelReason') }}</dt>
        <dd data-test="cancel-reason">{{ order.cancel_reason }}</dd>
      </div>
    </dl>

    <h2>{{ t('staffOrder.timeline') }}</h2>
    <OrderTimeline :history="order.history ?? []" />
  </div>
</template>

<style scoped>
.details {
  display: grid;
  gap: 0.75rem;
  margin: 1rem 0;
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
