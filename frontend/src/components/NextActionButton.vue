<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import * as ordersApi from '@/api/orders'
import { formMessage } from '@/utils/forms'

// The one valid next step of a driver's order (BL-032). The server decides the step;
// this only shows the matching button and sends the tap once.
const props = defineProps({ order: { type: Object, required: true } })
const emit = defineEmits(['updated'])
const { t } = useI18n()

const busy = ref(false)
const error = ref('')

async function advance() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    emit('updated', await ordersApi.advanceOrder(props.order.id))
  } catch (err) {
    error.value = formMessage(err, t)
    // The order moved or was cancelled elsewhere: let the screen reload it.
    if (err?.status === 400) emit('updated', null)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div v-if="order.next_action">
    <p v-if="error" class="form-error" role="alert" data-test="advance-error">{{ error }}</p>
    <button
      type="button"
      class="btn btn-primary next-action"
      data-test="advance"
      :disabled="busy"
      :aria-busy="busy"
      @click="advance"
    >
      {{ busy ? t('orders.updating') : t(`orders.actions.${order.next_action}`) }}
    </button>
  </div>
</template>

<style scoped>
.next-action {
  inline-size: 100%;
}
</style>
