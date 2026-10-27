<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import FormField from '@/components/FormField.vue'
import ListStatus from '@/components/ListStatus.vue'
import * as usersApi from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import {
  emailProblem,
  formMessage,
  phoneProblem,
  serverFieldErrors,
  clientError,
  errorText,
} from '@/utils/forms'

// One screen for /admin/users/new (create) and /admin/users/:id (edit and delete).
const { t, locale } = useI18n()
const msg = (e) => errorText(e, t)
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const id = computed(() => route.params.id)
const isEdit = computed(() => Boolean(id.value))

const ALL_ROLES = ['admin', 'manager', 'driver', 'trader', 'client']
const FIELDS = ['full_name', 'phone', 'username', 'email', 'password', 'role']

const loaded = ref(null)
const fullName = ref('')
const phone = ref('')
const username = ref('')
const email = ref('')
const password = ref('')
const role = ref('client')

const loading = ref(isEdit.value)
const loadError = ref('')
const offline = ref(false)
const submitting = ref(false)
const formError = ref('')
const saved = ref(false)
const fieldErrors = ref({})
const confirmingDelete = ref(false)

// A Manager never manages an Admin (BR-14): no Admin option, and an Admin target is read-only.
const roleOptions = computed(() =>
  auth.role === 'manager' ? ALL_ROLES.filter((r) => r !== 'admin') : ALL_ROLES,
)
const targetIsAdmin = computed(() => loaded.value?.role === 'admin')
const locked = computed(() => isEdit.value && auth.role === 'manager' && targetIsAdmin.value)
const isSelf = computed(() => isEdit.value && loaded.value?.id === auth.user?.id)
const needsUsername = computed(() => role.value === 'admin' || role.value === 'manager')
const canDelete = computed(() => isEdit.value && !locked.value && !isSelf.value)
const lastAction = computed(() => loaded.value?.last_action ?? null)

function formatDate(iso) {
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(
    new Date(iso),
  )
}

function fill(user) {
  loaded.value = user
  fullName.value = user.full_name ?? ''
  phone.value = user.phone ?? ''
  username.value = user.username ?? ''
  email.value = user.email ?? ''
  role.value = user.role
  password.value = ''
}

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    fill(await usersApi.getUser(id.value))
  } catch (err) {
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    loading.value = false
  }
}
onMounted(() => {
  if (isEdit.value) load()
})

function validate() {
  const errors = {}
  const name = fullName.value.trim()
  if (!name) errors.full_name = clientError('auth.register.errors.nameRequired')
  else if (name.length < 2) errors.full_name = clientError('auth.register.errors.nameShort')
  const p = phoneProblem(phone.value)
  if (p === 'required') errors.phone = clientError('auth.register.errors.phoneRequired')
  else if (p) errors.phone = clientError('auth.register.errors.phoneInvalid')
  if (emailProblem(email.value)) errors.email = clientError('auth.register.errors.emailInvalid')
  if (needsUsername.value && !username.value.trim())
    errors.username = clientError('admin.userForm.errors.usernameRequired')
  if (!isEdit.value && !password.value)
    errors.password = clientError('auth.register.errors.passwordRequired')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

// What the form holds now, trimmed. Status, is_staff and is_superuser are never part of it.
function current() {
  return {
    full_name: fullName.value.trim(),
    phone: phone.value.trim(),
    username: username.value.trim(),
    email: email.value.trim(),
    role: role.value,
  }
}

// Edit sends only the fields the person changed; a blank password means "leave it".
function dirtyFields() {
  const now = current()
  const before = {
    full_name: loaded.value.full_name ?? '',
    phone: loaded.value.phone ?? '',
    username: loaded.value.username ?? '',
    email: loaded.value.email ?? '',
    role: loaded.value.role,
  }
  const out = {}
  for (const key of Object.keys(now)) if (now[key] !== before[key]) out[key] = now[key]
  if (password.value) out.password = password.value
  return out
}

async function submit() {
  if (submitting.value || locked.value) return
  formError.value = ''
  saved.value = false
  if (!validate()) return
  submitting.value = true
  try {
    if (isEdit.value) {
      const changes = dirtyFields()
      if (Object.keys(changes).length) fill(await usersApi.updateUser(id.value, changes))
      saved.value = true
    } else {
      const body = { ...current(), password: password.value }
      if (!body.username) delete body.username
      if (!body.email) delete body.email
      await usersApi.createUser(body)
      await router.push('/admin/users')
    }
  } catch (err) {
    fieldErrors.value = serverFieldErrors(err, FIELDS)
    // A 403 (BR-14) or any other failure keeps every typed value in place.
    if (Object.keys(fieldErrors.value).length === 0) formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}

async function remove() {
  if (submitting.value) return
  submitting.value = true
  formError.value = ''
  try {
    await usersApi.deleteUser(id.value)
    await router.push('/admin/users')
  } catch (err) {
    confirmingDelete.value = false
    formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <h1>{{ isEdit ? t('admin.userForm.editTitle') : t('admin.userForm.createTitle') }}</h1>
    <p>
      <RouterLink to="/admin/users" class="touch-link">{{ t('admin.userForm.back') }}</RouterLink>
    </p>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />

    <template v-if="!loading && !loadError">
      <p v-if="saved" class="form-notice" role="status" data-test="saved">
        {{ t('admin.userForm.saved') }}
      </p>
      <p v-if="formError" class="form-error" role="alert" data-test="form-error">
        {{ formError }}
      </p>
      <p v-if="locked" class="form-notice" data-test="locked">
        {{ t('admin.userForm.adminLocked') }}
      </p>

      <dl v-if="isEdit" class="readonly">
        <div>
          <dt>{{ t('admin.users.status') }}</dt>
          <dd data-test="status">{{ t(`statuses.${loaded.status}`) }}</dd>
        </div>
        <div v-if="loaded.rejection_reason">
          <dt>{{ t('admin.userForm.rejectionReason') }}</dt>
          <dd data-test="rejection-reason">{{ loaded.rejection_reason }}</dd>
        </div>
        <div v-if="lastAction">
          <dt>{{ t('admin.userForm.lastAction') }}</dt>
          <dd data-test="last-action">
            {{ t(`admin.userForm.actions.${lastAction.action}`) }} · {{ lastAction.actor_name }} ·
            {{ formatDate(lastAction.created_at) }}
            <template v-if="lastAction.reason"> · {{ lastAction.reason }}</template>
          </dd>
        </div>
      </dl>

      <form class="app-form" novalidate @submit.prevent="submit">
        <FormField
          id="uf-full_name"
          v-model="fullName"
          name="full_name"
          :label="t('account.profile.name')"
          :error="msg(fieldErrors.full_name)"
          :disabled="submitting || locked"
          required
        />
        <FormField
          id="uf-phone"
          v-model="phone"
          type="tel"
          name="phone"
          inputmode="tel"
          dir="ltr"
          :label="t('auth.register.phone')"
          :hint="t('auth.register.phoneHint')"
          :error="msg(fieldErrors.phone)"
          :disabled="submitting || locked"
          required
        />
        <FormField
          id="uf-username"
          v-model="username"
          name="username"
          dir="ltr"
          :label="t('account.profile.username')"
          :hint="needsUsername ? t('admin.userForm.usernameHint') : ''"
          :error="msg(fieldErrors.username)"
          :disabled="submitting || locked"
          :required="needsUsername"
        />
        <FormField
          id="uf-email"
          v-model="email"
          type="email"
          name="email"
          dir="ltr"
          :label="t('account.profile.email')"
          :error="msg(fieldErrors.email)"
          :disabled="submitting || locked"
        />
        <FormField
          id="uf-password"
          v-model="password"
          type="password"
          name="password"
          autocomplete="new-password"
          dir="ltr"
          :label="t('admin.userForm.password')"
          :hint="isEdit ? t('admin.userForm.passwordKeep') : t('auth.register.passwordRules')"
          :error="msg(fieldErrors.password)"
          :disabled="submitting || locked"
          :required="!isEdit"
        />

        <div class="field">
          <label for="uf-role">{{ t('admin.users.role') }} *</label>
          <select
            id="uf-role"
            v-model="role"
            name="role"
            :disabled="submitting || locked || isSelf"
            :aria-invalid="fieldErrors.role ? 'true' : 'false'"
            :aria-describedby="fieldErrors.role ? 'uf-role-error' : undefined"
          >
            <option v-for="r in roleOptions" :key="r" :value="r">{{ t(`roles.${r}`) }}</option>
            <!-- An Admin target opened by an Admin keeps its own role in the list. -->
            <option v-if="isEdit && !roleOptions.includes(loaded.role)" :value="loaded.role">
              {{ t(`roles.${loaded.role}`) }}
            </option>
          </select>
          <p v-if="fieldErrors.role" id="uf-role-error" class="field-error" role="alert">
            {{ fieldErrors.role }}
          </p>
        </div>

        <div class="btn-row">
          <button
            v-if="!locked"
            type="submit"
            class="btn btn-primary"
            :disabled="submitting"
            :aria-busy="submitting"
          >
            {{ submitting ? t('account.profile.saving') : t('account.profile.save') }}
          </button>
          <button
            v-if="canDelete && !confirmingDelete"
            type="button"
            class="btn btn-danger"
            data-test="delete"
            :disabled="submitting"
            @click="confirmingDelete = true"
          >
            {{ t('admin.userForm.delete') }}
          </button>
        </div>
      </form>

      <div v-if="confirmingDelete" class="form-error" role="alertdialog" data-test="confirm-delete">
        <p>{{ t('admin.userForm.confirmDelete', { name: loaded.full_name }) }}</p>
        <div class="btn-row">
          <button
            type="button"
            class="btn btn-danger"
            data-test="confirm-yes"
            :disabled="submitting"
            @click="remove"
          >
            {{ t('admin.userForm.confirmYes') }}
          </button>
          <button
            type="button"
            class="btn"
            data-test="confirm-no"
            @click="confirmingDelete = false"
          >
            {{ t('common.cancel') }}
          </button>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.readonly {
  display: grid;
  gap: 0.5rem;
  margin: 0 0 1.5rem;
}
.readonly div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}
dt {
  font-weight: 600;
}
dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.field {
  display: grid;
  gap: 0.375rem;
}
label {
  font-weight: 600;
}
select {
  font: inherit;
  min-block-size: var(--touch-target);
  padding-inline: 0.5rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
  background: var(--color-surface);
  color: inherit;
}
.field-error {
  margin: 0;
  font-size: 0.875rem;
  color: #b42318;
}
</style>
