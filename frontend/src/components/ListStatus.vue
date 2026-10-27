<script setup>
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useOnline } from '@/composables/useOnline'

// Loading / error-with-retry / empty states shared by the admin lists (BL-065).
const props = defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  offline: { type: Boolean, default: false },
  empty: { type: Boolean, default: false },
  emptyText: { type: String, default: '' },
})
const emit = defineEmits(['retry'])
const { t } = useI18n()

// The offline text also follows the browser's own state, so it appears or goes away
// without a new request. Coming back online while an error is shown retries once.
const online = useOnline()
const showOffline = computed(() => props.offline || !online.value)
watch(online, (now, was) => {
  if (now && !was && props.error && !props.loading) emit('retry')
})
</script>

<template>
  <p v-if="loading" role="status" data-test="loading">{{ t('common.loading') }}</p>
  <div v-else-if="error" data-test="load-error">
    <p class="form-error" role="alert">{{ showOffline ? t('common.offline') : error }}</p>
    <button type="button" class="btn" data-test="retry" @click="$emit('retry')">
      {{ t('common.retry') }}
    </button>
  </div>
  <p v-else-if="empty" class="empty-state" data-test="empty">{{ emptyText }}</p>
</template>
