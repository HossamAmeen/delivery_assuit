<script setup>
import { useI18n } from 'vue-i18n'
import { formatDateTime } from '@/utils/format'

// The status history of an order (BL-027), oldest first.
defineProps({ history: { type: Array, default: () => [] } })
const { t, locale } = useI18n()
</script>

<template>
  <ol class="timeline" data-test="timeline">
    <li v-for="(h, i) in history" :key="i" data-test="step">
      <strong>{{ t(`orders.status.${h.to_status}`) }}</strong>
      <span>{{ formatDateTime(h.created_at, locale) }}</span>
      <span v-if="h.reason" class="reason">{{ h.reason }}</span>
    </li>
  </ol>
</template>

<style scoped>
.timeline {
  display: grid;
  gap: 0.5rem;
  padding-inline-start: 1.25rem;
}
.timeline li {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 0.75rem;
}
.reason {
  font-style: italic;
}
</style>
