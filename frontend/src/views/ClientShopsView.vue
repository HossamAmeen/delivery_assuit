<script setup>
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as shopsApi from '@/api/shops'
import { formMessage } from '@/utils/forms'

const { t } = useI18n()

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const search = ref('')
const page = ref(1)
const next = ref(null)
const previous = ref(null)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    const data = await shopsApi.listShops({ page: page.value, search: search.value.trim() })
    rows.value = data.results
    next.value = data.next
    previous.value = data.previous
  } catch (err) {
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    loading.value = false
  }
}
onMounted(load)

// A new search starts again at page 1.
let timer = null
watch(search, () => {
  page.value = 1
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})

function go(delta) {
  page.value += delta
  load()
}
</script>

<template>
  <section>
    <h1>{{ t('client.shops.title') }}</h1>

    <form class="filters" role="search" @submit.prevent="load">
      <label>
        {{ t('client.shops.search') }}
        <input v-model="search" type="search" name="search" data-test="search" />
      </label>
    </form>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('client.shops.empty')"
      @retry="load"
    />

    <ul v-if="!loading && !loadError && rows.length" class="shop-list">
      <li v-for="shop in rows" :key="shop.id" class="shop-row" data-test="row">
        <div>
          <strong>{{ shop.name }}</strong>
          <p v-if="shop.description" class="shop-desc">{{ shop.description }}</p>
        </div>
        <RouterLink :to="`/client/shops/${shop.id}`" class="btn touch-link" data-test="open">{{
          t('client.shops.open')
        }}</RouterLink>
      </li>
    </ul>

    <nav v-if="previous || next" class="pager" :aria-label="t('admin.users.pager')">
      <button type="button" class="btn" data-test="prev" :disabled="!previous" @click="go(-1)">
        {{ t('admin.users.previous') }}
      </button>
      <button type="button" class="btn" data-test="next" :disabled="!next" @click="go(1)">
        {{ t('admin.users.next') }}
      </button>
    </nav>
  </section>
</template>

<style scoped>
.filters {
  margin-block-end: 1rem;
}
label {
  display: grid;
  gap: 0.25rem;
  font-weight: 600;
}
input {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
}
.shop-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.shop-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.shop-desc {
  margin: 0.25rem 0 0;
}
.btn {
  text-decoration: none;
}
.pager {
  display: flex;
  gap: 0.5rem;
  margin-block-start: 1rem;
}
</style>
