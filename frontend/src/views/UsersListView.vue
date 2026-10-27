<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as usersApi from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import { formMessage } from '@/utils/forms'

const { t } = useI18n()
const auth = useAuthStore()

const ROLES = ['admin', 'manager', 'driver', 'trader', 'client']
const STATUSES = ['active', 'pending_approval', 'deactivated', 'rejected']

const rows = ref([])
const count = ref(0)
const next = ref(null)
const previous = ref(null)
const page = ref(1)
const role = ref('')
const status = ref('')
const search = ref('')
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const busyId = ref(null)
const actionError = ref('')

// The query that goes to the API: empty filters are left out by the api module.
const query = computed(() => ({
  page: page.value,
  role: role.value,
  status: status.value,
  search: search.value.trim(),
}))

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    const data = await usersApi.listUsers(query.value)
    rows.value = data.results
    count.value = data.count
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

// A new filter starts again at page 1.
let timer = null
watch([role, status, search], () => {
  page.value = 1
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})

function go(delta) {
  page.value += delta
  load()
}

// A Manager never manages an Admin (BR-14): hide the actions instead of calling the API.
function canManage(row) {
  return !(auth.role === 'manager' && row.role === 'admin')
}
const canActivate = (row) => row.status === 'deactivated' && canManage(row)
const canDeactivate = (row) => row.status === 'active' && canManage(row) && row.id !== auth.user?.id

async function act(row, call) {
  if (busyId.value) return
  busyId.value = row.id
  actionError.value = ''
  try {
    const user = await call(row.id)
    // The response is a full user; only the list fields are kept on the row.
    rows.value = rows.value.map((r) => (r.id === row.id ? { ...r, status: user.status } : r))
  } catch (err) {
    actionError.value = formMessage(err, t)
  } finally {
    busyId.value = null
  }
}
const activate = (row) => act(row, usersApi.activateUser)
// Deactivating blocks a person from the app, so it asks first (BL-068).
const confirmingId = ref(null)
const deactivate = async (row) => {
  confirmingId.value = null
  await act(row, usersApi.deactivateUser)
}
</script>

<template>
  <section>
    <div class="list-head">
      <h1>{{ t('admin.users.title') }}</h1>
      <RouterLink to="/admin/users/new" class="btn btn-primary" data-test="new-user">{{
        t('admin.users.new')
      }}</RouterLink>
    </div>

    <form class="filters" role="search" @submit.prevent="load">
      <label>
        {{ t('admin.users.search') }}
        <input v-model="search" type="search" name="search" data-test="search" />
      </label>
      <label>
        {{ t('admin.users.role') }}
        <select v-model="role" data-test="role-filter">
          <option value="">{{ t('admin.users.all') }}</option>
          <option v-for="r in ROLES" :key="r" :value="r">{{ t(`roles.${r}`) }}</option>
        </select>
      </label>
      <label>
        {{ t('admin.users.status') }}
        <select v-model="status" data-test="status-filter">
          <option value="">{{ t('admin.users.all') }}</option>
          <option v-for="s in STATUSES" :key="s" :value="s">{{ t(`statuses.${s}`) }}</option>
        </select>
      </label>
    </form>

    <p v-if="actionError" class="form-error" role="alert" data-test="action-error">
      {{ actionError }}
    </p>

    <ListStatus
      :loading="loading"
      :error="loadError"
      :offline="offline"
      :empty="!loading && !loadError && rows.length === 0"
      :empty-text="t('admin.users.empty')"
      @retry="load"
    />

    <div v-if="!loading && !loadError && rows.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">{{ t('account.profile.name') }}</th>
            <th scope="col">{{ t('auth.register.phone') }}</th>
            <th scope="col">{{ t('admin.users.role') }}</th>
            <th scope="col">{{ t('admin.users.status') }}</th>
            <th scope="col">
              <span class="visually-hidden">{{ t('admin.users.actions') }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" data-test="row">
            <td>
              <RouterLink :to="`/admin/users/${row.id}`" class="touch-link" data-test="open">{{
                row.full_name
              }}</RouterLink>
            </td>
            <td dir="ltr">{{ row.phone }}</td>
            <td>{{ t(`roles.${row.role}`) }}</td>
            <td data-test="status">{{ t(`statuses.${row.status}`) }}</td>
            <td class="btn-row">
              <button
                v-if="canActivate(row)"
                type="button"
                class="btn"
                data-test="activate"
                :disabled="busyId === row.id"
                @click="activate(row)"
              >
                {{ t('admin.users.activate') }}
              </button>
              <template v-if="canDeactivate(row) && confirmingId === row.id">
                <span role="alertdialog">{{ t('admin.users.confirmDeactivate') }}</span>
                <button
                  type="button"
                  class="btn btn-danger"
                  data-test="confirm-deactivate"
                  :disabled="busyId === row.id"
                  @click="deactivate(row)"
                >
                  {{ t('admin.userForm.confirmYes') }}
                </button>
                <button type="button" class="btn" data-test="keep" @click="confirmingId = null">
                  {{ t('common.cancel') }}
                </button>
              </template>
              <button
                v-else-if="canDeactivate(row)"
                type="button"
                class="btn btn-danger"
                data-test="deactivate"
                :disabled="busyId === row.id"
                @click="confirmingId = row.id"
              >
                {{ t('admin.users.deactivate') }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <nav
      v-if="!loading && !loadError && count > 0"
      class="pager"
      :aria-label="t('admin.users.pager')"
    >
      <button type="button" class="btn" data-test="prev" :disabled="!previous" @click="go(-1)">
        {{ t('admin.users.prev') }}
      </button>
      <span data-test="page">{{ t('admin.users.pageOf', { page, count }) }}</span>
      <button type="button" class="btn" data-test="next" :disabled="!next" @click="go(1)">
        {{ t('admin.users.next') }}
      </button>
    </nav>
  </section>
</template>

<style scoped>
.list-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-block: 1rem;
}
.filters label {
  display: grid;
  gap: 0.25rem;
  font-weight: 600;
}
.filters input,
.filters select {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.5rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
  color: inherit;
}
.table-wrap {
  overflow-x: auto;
}
table {
  inline-size: 100%;
  border-collapse: collapse;
}
th,
td {
  padding: 0.5rem;
  text-align: start;
  border-block-end: 1px solid var(--color-border);
}
.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-block-start: 1rem;
}
.visually-hidden {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}
</style>
