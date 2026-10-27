<script setup>
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import OrderDetails from '@/components/OrderDetails.vue'
import * as ordersApi from '@/api/orders'
import { ApiError } from '@/api/http'
import { clientError, errorText, formMessage, serverFieldErrors } from '@/utils/forms'

// A client's order (BL-050): status, driver name, timeline, and cancel / edit only before
// a driver is assigned (BR-12, BR-13).
const { t } = useI18n()
const msg = (e) => errorText(e, t)
const route = useRoute()
const id = computed(() => route.params.id)

const order = ref(null)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const missing = ref(false)
const confirming = ref(false)
const reason = ref('')
const busy = ref(false)
const actionError = ref('')
const notice = ref('')
// rating form (BL-051): only on a delivered order that has no rating yet
const score = ref(0)
const comment = ref('')
const ratingError = ref(null)
const rating = ref(false)

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

const changeable = computed(() => ['created', 'available'].includes(order.value?.status))
const waitingText = computed(() => {
  if (order.value?.status === 'created') return t('clientOrder.waitingReview')
  if (order.value?.status === 'available') return t('clientOrder.waitingDriver')
  return ''
})

const rateable = computed(() => order.value?.status === 'delivered' && !order.value?.rating)

async function submitRating() {
  if (rating.value) return
  actionError.value = ''
  if (!score.value) {
    ratingError.value = clientError('clientOrder.scoreRequired')
    return
  }
  ratingError.value = null
  rating.value = true
  try {
    await ordersApi.rateOrder(order.value.id, score.value, comment.value.trim())
    notice.value = t('clientOrder.thanks')
    await load()
  } catch (err) {
    const f = serverFieldErrors(err, ['score', 'comment', 'status'])
    ratingError.value = f.score ?? f.comment ?? null
    if (!ratingError.value) actionError.value = f.status || formMessage(err, t)
    // Rated meanwhile (or no longer rateable): show the real state.
    if (err?.status === 400 && f.status) await load()
  } finally {
    rating.value = false
  }
}

async function cancel() {
  if (busy.value) return
  busy.value = true
  actionError.value = ''
  notice.value = ''
  try {
    await ordersApi.cancelOrder(order.value.id, reason.value.trim())
    confirming.value = false
    reason.value = ''
    notice.value = t('clientOrder.cancelled')
    await load()
  } catch (err) {
    actionError.value = formMessage(err, t)
    // A driver was assigned meanwhile: show the real state, without the buttons.
    if (err?.status === 403 || err?.status === 400) await load()
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <p>
      <RouterLink to="/client/orders" class="touch-link">{{ t('orders.backToList') }}</RouterLink>
    </p>
    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />
    <div v-if="missing" class="form-notice" role="status" data-test="missing">
      {{ t('orders.notFound') }}
    </div>

    <template v-if="order && !loading">
      <h1 dir="ltr" data-test="reference">{{ order.reference }}</h1>
      <p v-if="notice" class="form-notice" role="status" data-test="notice">{{ notice }}</p>
      <p v-if="actionError" class="form-error" role="alert" data-test="action-error">
        {{ actionError }}
      </p>
      <p v-if="waitingText" class="form-notice" role="status" data-test="waiting">
        {{ waitingText }}
      </p>
      <p>
        <button type="button" class="btn" data-test="refresh" @click="load">
          {{ t('orders.refresh') }}
        </button>
      </p>

      <OrderDetails :order="order" />

      <section v-if="order.rating" class="rating" data-test="your-rating">
        <h2>{{ t('clientOrder.yourRating') }}</h2>
        <p data-test="rating-score">{{ t('clientOrder.outOf', { score: order.rating.score }) }}</p>
        <p v-if="order.rating.comment" data-test="rating-comment">{{ order.rating.comment }}</p>
      </section>

      <form
        v-if="rateable"
        class="rating"
        novalidate
        data-test="rating-form"
        @submit.prevent="submitRating"
      >
        <h2>{{ t('clientOrder.rateTitle') }}</h2>
        <fieldset class="stars">
          <legend>{{ t('clientOrder.score') }}</legend>
          <label v-for="n in 5" :key="n" class="star">
            <input
              v-model="score"
              type="radio"
              name="score"
              :value="n"
              :disabled="rating"
              :data-test="`score-${n}`"
            />
            {{ n }}
          </label>
        </fieldset>
        <p v-if="ratingError" class="field-error" role="alert" data-test="rating-error">
          {{ msg(ratingError) }}
        </p>
        <label for="rating-comment">{{ t('clientOrder.comment') }}</label>
        <textarea
          id="rating-comment"
          v-model="comment"
          rows="2"
          maxlength="500"
          dir="auto"
          :disabled="rating"
        />
        <button
          type="submit"
          class="btn btn-primary"
          data-test="rate"
          :disabled="rating"
          :aria-busy="rating"
        >
          {{ t('clientOrder.rate') }}
        </button>
      </form>

      <div v-if="changeable" class="actions">
        <RouterLink
          :to="`/client/orders/${order.id}/edit`"
          class="btn touch-link"
          data-test="edit"
          >{{ t('clientOrder.edit') }}</RouterLink
        >
        <div v-if="confirming" class="field">
          <label for="cancel-reason">{{ t('clientOrder.reason') }}</label>
          <input
            id="cancel-reason"
            v-model="reason"
            type="text"
            maxlength="500"
            :disabled="busy"
            data-test="reason"
          />
          <div class="btn-row">
            <button
              type="button"
              class="btn btn-danger"
              data-test="confirm-cancel"
              :disabled="busy"
              :aria-busy="busy"
              @click="cancel"
            >
              {{ t('clientOrder.confirmCancel') }}
            </button>
            <button type="button" class="btn" data-test="keep" @click="confirming = false">
              {{ t('clientOrder.keep') }}
            </button>
          </div>
        </div>
        <button
          v-else
          type="button"
          class="btn btn-danger"
          data-test="cancel"
          @click="confirming = true"
        >
          {{ t('clientOrder.cancel') }}
        </button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.rating {
  display: grid;
  gap: 0.5rem;
  margin-block: 1rem;
}
.stars {
  display: flex;
  gap: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
}
.star {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  min-block-size: var(--touch-target);
}
textarea {
  font: inherit;
  padding: 0.5rem 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
}
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
.actions {
  display: grid;
  gap: 0.75rem;
}
.field {
  display: grid;
  gap: 0.375rem;
}
label {
  font-weight: 600;
}
input {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
}
.btn {
  text-decoration: none;
}
</style>
