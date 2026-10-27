<script setup>
import { computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useHealthStore } from '@/stores/health'

const { t, locale } = useI18n()
const store = useHealthStore()
onMounted(() => store.check())
// Re-fetch on language change so a server message is shown in the new language.
watch(locale, () => {
  if (store.status === 'error') store.check()
})

const errorText = computed(() => {
  if (!store.error) return ''
  if (store.error.isNetworkError) return t('health.errors.network')
  // Server envelope message is already localized by the backend.
  if (store.error.message) return store.error.message
  if (store.error.status === 403) return t('health.errors.rejected')
  if (store.error.status === 429) return t('health.errors.rateLimited')
  return t('health.errors.unavailable')
})
</script>

<template>
  <section class="health" aria-live="polite" data-testid="health-status">
    <p v-if="store.status === 'loading' || store.status === 'idle'">{{ t('health.checking') }}</p>
    <p v-else-if="store.status === 'healthy'" class="ok">{{ t('health.healthy') }}</p>
    <div v-else class="error" role="alert">
      <p>{{ errorText }}</p>
      <button type="button" @click="store.check()">{{ t('health.retry') }}</button>
    </div>
  </section>
</template>
