<script setup>
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import OrderDetails from '@/components/OrderDetails.vue'
import * as ordersApi from '@/api/orders'
import { ApiError } from '@/api/http'
import { formMessage } from '@/utils/forms'

// One order placed to the trader's shop. Read only: a trader cannot create, edit or cancel (BL-038).
const { t } = useI18n()
const route = useRoute()
const id = computed(() => route.params.id)

const order = ref(null)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const missing = ref(false)

// `silent` refreshes quietly (auto-refresh): no spinner, errors are ignored so the screen stays.
async function load({ silent = false } = {}) {
  if (!silent) loading.value = true
  if (!silent) loadError.value = ''
  if (!silent) offline.value = false
  if (!silent) missing.value = false
  try {
    order.value = await ordersApi.getOrder(id.value)
  } catch (err) {
    if (silent) return
    if (err instanceof ApiError && err.status === 404) missing.value = true
    else {
      offline.value = Boolean(err?.isNetworkError)
      loadError.value = formMessage(err, t)
    }
  } finally {
    if (!silent) loading.value = false
  }
}
onMounted(load)
useAutoRefresh(() => load({ silent: true }))
</script>

<template>
  <section class="form-page">
    <p>
      <RouterLink to="/trader/orders" class="touch-link">{{ t('orders.backToList') }}</RouterLink>
    </p>
    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />
    <div v-if="missing" class="form-notice" role="status" data-test="missing">
      {{ t('orders.notFound') }}
    </div>
    <template v-if="order && !loading">
      <h1 dir="ltr" data-test="reference">{{ order.reference }}</h1>
      <p>
        <button type="button" class="btn" data-test="refresh" @click="load">
          {{ t('orders.refresh') }}
        </button>
      </p>
      <OrderDetails :order="order" />
    </template>
  </section>
</template>
