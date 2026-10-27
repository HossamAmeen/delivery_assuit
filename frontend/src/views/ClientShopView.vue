<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as shopsApi from '@/api/shops'
import { ApiError } from '@/api/http'
import { formMessage } from '@/utils/forms'

const { t } = useI18n()
const route = useRoute()
const id = computed(() => route.params.id)

const shop = ref(null)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
// A closed shop (or an unknown id) is a 404: say it is unavailable instead of a failure.
const unavailable = ref(false)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  unavailable.value = false
  try {
    shop.value = await shopsApi.getShop(id.value)
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) unavailable.value = true
    else {
      offline.value = Boolean(err?.isNetworkError)
      loadError.value = formMessage(err, t)
    }
  } finally {
    loading.value = false
  }
}
onMounted(load)

const priceText = (price) => (price === null || price === undefined ? '' : String(price))
</script>

<template>
  <section class="form-page">
    <p>
      <RouterLink to="/client/shops" class="touch-link">{{ t('client.shops.back') }}</RouterLink>
    </p>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />

    <div v-if="unavailable" class="form-notice" role="status" data-test="unavailable">
      {{ t('client.shops.unavailable') }}
    </div>

    <template v-if="shop && !loading">
      <h1>{{ shop.name }}</h1>
      <p v-if="shop.description" data-test="description">{{ shop.description }}</p>

      <h2>{{ t('client.shops.items') }}</h2>
      <p v-if="shop.items.length === 0" class="empty-state" data-test="no-items">
        {{ t('client.shops.noItems') }}
      </p>
      <ul v-else class="items">
        <li v-for="item in shop.items" :key="item.id" data-test="item">
          <strong>{{ item.name }}</strong>
          <span v-if="priceText(item.price)" class="price" data-test="price">{{
            priceText(item.price)
          }}</span>
          <p v-if="item.description" class="item-desc">{{ item.description }}</p>
        </li>
      </ul>

      <p>
        <RouterLink
          v-if="shop.items.length"
          :to="`/client/shops/${shop.id}/order`"
          class="btn btn-primary touch-link"
          data-test="order"
          >{{ t('client.shops.order') }}</RouterLink
        >
      </p>
    </template>
  </section>
</template>

<style scoped>
.items {
  display: grid;
  gap: 0.5rem;
  padding: 0;
  list-style: none;
}
.items li {
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.price {
  margin-inline-start: 0.5rem;
}
.item-desc {
  margin: 0.25rem 0 0;
}
.btn {
  text-decoration: none;
}
</style>
