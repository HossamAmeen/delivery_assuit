<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as notificationsApi from '@/api/notifications'
import { useAuthStore } from '@/stores/auth'
import { formMessage } from '@/utils/forms'
import { formatDateTime } from '@/utils/format'

// My notifications (BL-066): newest first, mark one or all as read, open the order.
const { t, locale } = useI18n()
const auth = useAuthStore()

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const actionError = ref('')
const page = ref(1)
const next = ref(null)
const previous = ref(null)
const unreadOnly = ref(false)
const busy = ref(false)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    const data = await notificationsApi.listNotifications({
      page: page.value,
      unread: unreadOnly.value ? 'true' : '',
    })
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

function go(delta) {
  page.value += delta
  load()
}
function toggleUnread() {
  page.value = 1
  load()
}

// Where an order notification leads, by role. Account notifications go to the approvals queue.
const base = computed(
  () => ({ client: '/client', trader: '/trader', driver: '/driver' })[auth.role] ?? '/admin',
)
function target(n) {
  if (!n.order_id) return '/admin/approvals'
  return auth.role === 'driver'
    ? `/driver/orders/${n.order_id}`
    : `${base.value}/orders/${n.order_id}`
}
const text = (n) => t(`notifications.kinds.${n.kind}`, { reference: n.reference ?? '' })

async function open(n) {
  if (n.read) return
  try {
    await notificationsApi.markRead(n.id)
    n.read = true
  } catch {
    // opening the order still works; the count fixes itself on the next refresh
  }
}

async function readAll() {
  if (busy.value) return
  busy.value = true
  actionError.value = ''
  try {
    await notificationsApi.markAllRead()
    rows.value.forEach((n) => (n.read = true))
  } catch (err) {
    actionError.value = formMessage(err, t)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <h1>{{ t('notifications.title') }}</h1>
    <p v-if="actionError" class="form-error" role="alert" data-test="action-error">
      {{ actionError }}
    </p>

    <div class="tools">
      <label class="check">
        <input
          v-model="unreadOnly"
          type="checkbox"
          data-test="unread-only"
          @change="toggleUnread"
        />
        {{ t('notifications.unreadOnly') }}
      </label>
      <button type="button" class="btn" data-test="read-all" :disabled="busy" @click="readAll">
        {{ t('notifications.readAll') }}
      </button>
    </div>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('notifications.empty')"
      @retry="load"
    />

    <ul v-if="!loading && !loadError && rows.length" class="list">
      <li v-for="n in rows" :key="n.id" :class="['item', { unread: !n.read }]" data-test="item">
        <RouterLink :to="target(n)" class="touch-link" data-test="open" @click="open(n)">{{
          text(n)
        }}</RouterLink>
        <span class="when">{{ formatDateTime(n.created_at, locale) }}</span>
        <span v-if="!n.read" class="role-badge" data-test="unread">{{
          t('notifications.new')
        }}</span>
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
.tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-block-end: 1rem;
}
.check {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-block-size: var(--touch-target);
}
.check input {
  inline-size: 1.25rem;
  block-size: 1.25rem;
}
.list {
  display: grid;
  gap: 0.5rem;
  padding: 0;
  list-style: none;
}
.item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.item.unread {
  border-inline-start: 4px solid var(--color-primary);
  font-weight: 600;
}
.when {
  font-size: 0.875rem;
  color: #52606d;
}
.pager {
  display: flex;
  gap: 0.5rem;
  margin-block-start: 1rem;
}
</style>
