<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import FormField from '@/components/FormField.vue'
import ListStatus from '@/components/ListStatus.vue'
import * as shopApi from '@/api/shop'
import { clientError, errorText, formMessage, serverFieldErrors } from '@/utils/forms'

const { t } = useI18n()
const msg = (e) => errorText(e, t)

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const pageError = ref('')

// The form is closed (null), a new item ('new'), or the id being edited.
const editing = ref(null)
const name = ref('')
const description = ref('')
const fieldErrors = ref({})
const formError = ref('')
const submitting = ref(false)
const confirmingId = ref(null)
const busyId = ref(null)

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    rows.value = (await shopApi.listItems({ page_size: 100 })).results
  } catch (err) {
    offline.value = Boolean(err?.isNetworkError)
    loadError.value = formMessage(err, t)
  } finally {
    loading.value = false
  }
}
onMounted(load)

function openForm(row) {
  editing.value = row ? row.id : 'new'
  name.value = row?.name ?? ''
  description.value = row?.description ?? ''
  fieldErrors.value = {}
  formError.value = ''
}

function validate() {
  const errors = {}
  const n = name.value.trim()
  if (!n) errors.name = clientError('shop.items.errors.nameRequired')
  else if (n.length < 2) errors.name = clientError('shop.items.errors.nameShort')
  if (description.value.length > 300)
    errors.description = clientError('shop.items.errors.descriptionLong')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  if (!validate()) return
  submitting.value = true
  const body = { name: name.value.trim(), description: description.value.trim() }
  try {
    if (editing.value === 'new') await shopApi.createItem(body)
    else await shopApi.updateItem(editing.value, body)
    editing.value = null
    await load()
  } catch (err) {
    fieldErrors.value = serverFieldErrors(err, ['name', 'description'])
    if (Object.keys(fieldErrors.value).length === 0) formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}

async function toggleHidden(row) {
  if (busyId.value) return
  busyId.value = row.id
  pageError.value = ''
  try {
    const updated = await shopApi.updateItem(row.id, { is_hidden: !row.is_hidden })
    rows.value = rows.value.map((r) => (r.id === row.id ? updated : r))
  } catch (err) {
    pageError.value = formMessage(err, t)
  } finally {
    busyId.value = null
  }
}

async function remove(id) {
  if (busyId.value) return
  busyId.value = id
  pageError.value = ''
  try {
    await shopApi.deleteItem(id)
    confirmingId.value = null
    rows.value = rows.value.filter((r) => r.id !== id)
  } catch (err) {
    confirmingId.value = null
    pageError.value = formMessage(err, t)
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <section class="form-page">
    <h1>{{ t('shop.items.title') }}</h1>
    <p>{{ t('shop.items.intro') }}</p>
    <p v-if="pageError" class="form-error" role="alert" data-test="page-error">{{ pageError }}</p>

    <div v-if="editing !== null">
      <h2 data-test="form-title">
        {{ editing === 'new' ? t('shop.items.add') : t('shop.items.edit') }}
      </h2>
      <p v-if="formError" class="form-error" role="alert" data-test="form-error">
        {{ formError }}
      </p>
      <form class="app-form" novalidate data-test="form" @submit.prevent="submit">
        <FormField
          id="item-name"
          name="name"
          :label="t('shop.items.name')"
          :model-value="name"
          :error="msg(fieldErrors.name)"
          :disabled="submitting"
          required
          @update:model-value="name = $event"
        />
        <FormField
          id="item-description"
          name="description"
          :label="t('shop.items.description')"
          :model-value="description"
          :error="msg(fieldErrors.description)"
          :disabled="submitting"
          @update:model-value="description = $event"
        />
        <div class="btn-row">
          <button
            type="submit"
            class="btn btn-primary"
            data-test="save"
            :disabled="submitting"
            :aria-busy="submitting"
          >
            {{ submitting ? t('account.profile.saving') : t('account.profile.save') }}
          </button>
          <button type="button" class="btn" data-test="cancel" @click="editing = null">
            {{ t('common.cancel') }}
          </button>
        </div>
      </form>
    </div>

    <template v-else>
      <p>
        <button type="button" class="btn btn-primary" data-test="add" @click="openForm(null)">
          {{ t('shop.items.add') }}
        </button>
      </p>

      <ListStatus
        :loading="loading"
        :error="loadError"
        :offline="offline"
        :empty="!loading && !loadError && rows.length === 0"
        :empty-text="t('shop.items.empty')"
        @retry="load"
      />

      <ul v-if="!loading && !loadError && rows.length" class="item-list">
        <li v-for="row in rows" :key="row.id" class="item-row" data-test="row">
          <div>
            <strong>{{ row.name }}</strong>
            <span v-if="row.is_hidden" class="role-badge" data-test="badge-hidden">{{
              t('shop.items.hiddenBadge')
            }}</span>
            <p v-if="row.description" class="item-desc">{{ row.description }}</p>
          </div>

          <div v-if="confirmingId === row.id" class="form-error" role="alertdialog">
            <p>{{ t('shop.items.confirmDelete') }}</p>
            <div class="btn-row">
              <button
                type="button"
                class="btn btn-danger"
                data-test="confirm-yes"
                :disabled="busyId === row.id"
                @click="remove(row.id)"
              >
                {{ t('admin.userForm.confirmYes') }}
              </button>
              <button type="button" class="btn" data-test="confirm-no" @click="confirmingId = null">
                {{ t('common.cancel') }}
              </button>
            </div>
          </div>
          <div v-else class="btn-row">
            <button type="button" class="btn" data-test="edit" @click="openForm(row)">
              {{ t('shop.items.edit') }}
            </button>
            <button
              type="button"
              class="btn"
              data-test="toggle-hidden"
              :disabled="busyId === row.id"
              @click="toggleHidden(row)"
            >
              {{ row.is_hidden ? t('shop.items.show') : t('shop.items.hide') }}
            </button>
            <button
              type="button"
              class="btn btn-danger"
              data-test="delete"
              @click="confirmingId = row.id"
            >
              {{ t('admin.userForm.delete') }}
            </button>
          </div>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.item-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.item-row {
  display: grid;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.item-desc {
  margin: 0.25rem 0 0;
}
</style>
