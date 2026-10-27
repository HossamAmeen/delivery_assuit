<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ListStatus from '@/components/ListStatus.vue'
import * as usersApi from '@/api/users'
import { formMessage, serverFieldErrors } from '@/utils/forms'

const { t } = useI18n()

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const busyId = ref(null)
const actionError = ref('')
// The row being rejected, and the optional reason typed for it.
const rejectingId = ref(null)
const reason = ref('')
const reasonError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    const data = await usersApi.listUsers({ status: 'pending_approval', page_size: 100 })
    rows.value = data.results
  } catch (err) {
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    loading.value = false
  }
}
onMounted(load)

function drop(id) {
  rows.value = rows.value.filter((r) => r.id !== id)
}

async function act(id, call) {
  if (busyId.value) return
  busyId.value = id
  actionError.value = ''
  reasonError.value = ''
  try {
    await call()
    drop(id)
    rejectingId.value = null
    reason.value = ''
  } catch (err) {
    // A too-long reason is a field error on the reject box, not a page error.
    reasonError.value = serverFieldErrors(err, ['reason']).reason ?? ''
    actionError.value = reasonError.value ? '' : formMessage(err, t)
  } finally {
    busyId.value = null
  }
}

const approve = (id) => act(id, () => usersApi.approveUser(id))
const reject = (id) => act(id, () => usersApi.rejectUser(id, reason.value.trim()))

function startReject(id) {
  rejectingId.value = id
  reason.value = ''
  actionError.value = ''
}
</script>

<template>
  <section>
    <h1>{{ t('admin.approvals.title') }}</h1>
    <p v-if="actionError" class="form-error" role="alert" data-test="action-error">
      {{ actionError }}
    </p>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('admin.approvals.empty')"
      @retry="load"
    />

    <ul v-if="!loading && !loadError && rows.length" class="approval-list">
      <li v-for="row in rows" :key="row.id" class="approval-row" data-test="row">
        <div class="approval-info">
          <strong>{{ row.full_name }}</strong>
          <span class="role-badge">{{ t(`roles.${row.role}`) }}</span>
          <span dir="ltr">{{ row.phone }}</span>
          <span v-if="row.email" dir="ltr">{{ row.email }}</span>
        </div>

        <div v-if="rejectingId === row.id" class="reject-box">
          <label :for="`reason-${row.id}`">{{ t('admin.approvals.reason') }}</label>
          <input
            :id="`reason-${row.id}`"
            v-model="reason"
            type="text"
            maxlength="500"
            :disabled="busyId === row.id"
            :aria-invalid="reasonError ? 'true' : 'false'"
            :aria-describedby="reasonError ? `reason-${row.id}-error` : undefined"
          />
          <p v-if="reasonError" :id="`reason-${row.id}-error`" class="reason-error" role="alert">
            {{ reasonError }}
          </p>
          <div class="btn-row">
            <button
              type="button"
              class="btn btn-danger"
              data-test="confirm-reject"
              :disabled="busyId === row.id"
              @click="reject(row.id)"
            >
              {{ t('admin.approvals.confirmReject') }}
            </button>
            <button type="button" class="btn" @click="rejectingId = null">
              {{ t('common.cancel') }}
            </button>
          </div>
        </div>

        <div v-else class="btn-row">
          <button
            type="button"
            class="btn btn-primary"
            data-test="approve"
            :disabled="busyId === row.id"
            @click="approve(row.id)"
          >
            {{ t('admin.approvals.approve') }}
          </button>
          <button
            type="button"
            class="btn btn-danger"
            data-test="reject"
            :disabled="busyId === row.id"
            @click="startReject(row.id)"
          >
            {{ t('admin.approvals.reject') }}
          </button>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.approval-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.approval-row {
  display: grid;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
}
.approval-info {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
  overflow-wrap: anywhere;
}
.reason-error {
  margin: 0;
  font-size: 0.875rem;
  color: #b42318;
}
.reject-box {
  display: grid;
  gap: 0.5rem;
}
.reject-box input {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
}
</style>
