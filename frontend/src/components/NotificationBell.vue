<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import * as notificationsApi from '@/api/notifications'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

// The bell in the header: a link to the notifications with the unread count (BL-066).
const { t } = useI18n()
const count = ref(0)

async function load() {
  count.value = await notificationsApi.getUnreadCount()
}
onMounted(() => load().catch(() => {}))
useAutoRefresh(load, { interval: 30000 })
</script>

<template>
  <RouterLink
    to="/notifications"
    class="bell"
    data-testid="notifications-link"
    :aria-label="count ? t('notifications.bellUnread', { n: count }) : t('notifications.bell')"
  >
    <span aria-hidden="true">🔔</span>
    <span v-if="count" class="badge" data-testid="notifications-count">{{
      count > 99 ? '99+' : count
    }}</span>
  </RouterLink>
</template>

<style scoped>
.bell {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-block-size: var(--touch-target);
  min-inline-size: var(--touch-target);
  text-decoration: none;
}
.badge {
  position: absolute;
  inset-block-start: 0.125rem;
  inset-inline-end: 0;
  min-inline-size: 1.25rem;
  padding-inline: 0.25rem;
  border-radius: 1rem;
  background: #b42318;
  color: #fff;
  font-size: 0.75rem;
  line-height: 1.25rem;
  text-align: center;
}
</style>
