<script setup>
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ListStatus from '@/components/ListStatus.vue'
import * as staffApi from '@/api/staff'
import { formMessage } from '@/utils/forms'
import { formatDateTime } from '@/utils/format'

// The audit log (BL-069): who did what and when. Read only for Admin and Manager.
const { t, te, locale } = useI18n()
// Dots would be read as a path by vue-i18n, so labels are keyed with underscores.
const label = (a) => `audit.actions.${a.replace('.', '_')}`
const ACTIONS = [
  'order.status',
  'order.fee',
  'order.rating',
  'item.price',
  'account.approved',
  'account.rejected',
  'account.activated',
  'account.deactivated',
]

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const action = ref('')
const page = ref(1)
const next = ref(null)
const previous = ref(null)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    const data = await staffApi.listAudit({ action: action.value, page: page.value })
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
watch(action, () => {
  page.value = 1
  load()
})
function go(delta) {
  page.value += delta
  load()
}
</script>

<template>
  <section>
    <h1>{{ t('audit.title') }}</h1>

    <label class="filter">
      {{ t('audit.action') }}
      <select v-model="action" data-test="action-filter">
        <option value="">{{ t('admin.users.all') }}</option>
        <option v-for="a in ACTIONS" :key="a" :value="a">{{ t(label(a)) }}</option>
      </select>
    </label>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('audit.empty')"
      @retry="load"
    />

    <div v-if="!loading && !loadError && rows.length" class="scroll">
      <table class="audit">
        <caption class="sr-only">
          {{
            t('audit.title')
          }}
        </caption>
        <thead>
          <tr>
            <th scope="col">{{ t('audit.when') }}</th>
            <th scope="col">{{ t('audit.who') }}</th>
            <th scope="col">{{ t('audit.action') }}</th>
            <th scope="col">{{ t('audit.target') }}</th>
            <th scope="col">{{ t('audit.detail') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id" data-test="row">
            <td>{{ formatDateTime(r.created_at, locale) }}</td>
            <td data-test="actor">{{ r.actor ? r.actor.full_name : '—' }}</td>
            <td data-test="action">{{ te(label(r.action)) ? t(label(r.action)) : r.action }}</td>
            <td dir="ltr" data-test="target">{{ r.target_type }} #{{ r.target_id }}</td>
            <td data-test="detail">{{ r.detail }}</td>
          </tr>
        </tbody>
      </table>
    </div>

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
.filter {
  display: grid;
  gap: 0.25rem;
  font-weight: 600;
  margin-block-end: 1rem;
  max-inline-size: 20rem;
}
select {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.5rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
}
.scroll {
  overflow-x: auto;
}
.audit {
  inline-size: 100%;
  border-collapse: collapse;
}
th,
td {
  padding: 0.5rem;
  text-align: start;
  border-block-end: 1px solid var(--color-border);
}
.sr-only {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}
.pager {
  display: flex;
  gap: 0.5rem;
  margin-block-start: 1rem;
}
</style>
