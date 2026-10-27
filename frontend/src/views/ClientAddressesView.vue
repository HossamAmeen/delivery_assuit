<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ListStatus from '@/components/ListStatus.vue'
import PlaceFields from '@/components/PlaceFields.vue'
import * as addressesApi from '@/api/addresses'
import { errorText, formMessage, serverFieldErrors } from '@/utils/forms'
import { emptyPlace, placePayload, placeProblems, placeToForm } from '@/utils/places'

const { t } = useI18n()
const msg = (e) => errorText(e, t)

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const pageError = ref('')

// The form is closed (null), a new address ('new'), or the id being edited.
const editing = ref(null)
const place = ref(emptyPlace())
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
    rows.value = (await addressesApi.listAddresses({ page_size: 100 })).results
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
  place.value = row ? placeToForm(row) : emptyPlace()
  fieldErrors.value = {}
  formError.value = ''
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  fieldErrors.value = placeProblems(place.value)
  if (Object.keys(fieldErrors.value).length) return
  submitting.value = true
  const body = placePayload(place.value)
  try {
    if (editing.value === 'new') await addressesApi.createAddress(body)
    else await addressesApi.updateAddress(editing.value, body)
    editing.value = null
    await load()
  } catch (err) {
    fieldErrors.value = serverFieldErrors(err, ['name', 'address', 'latitude', 'longitude'])
    if (Object.keys(fieldErrors.value).length === 0) formError.value = formMessage(err, t)
  } finally {
    submitting.value = false
  }
}

async function remove(id) {
  if (busyId.value) return
  busyId.value = id
  pageError.value = ''
  try {
    await addressesApi.deleteAddress(id)
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
    <h1>{{ t('client.addresses.title') }}</h1>
    <p>{{ t('client.addresses.intro') }}</p>
    <p v-if="pageError" class="form-error" role="alert" data-test="page-error">{{ pageError }}</p>

    <div v-if="editing !== null">
      <h2 data-test="form-title">
        {{ editing === 'new' ? t('client.addresses.add') : t('client.addresses.edit') }}
      </h2>
      <p v-if="formError" class="form-error" role="alert" data-test="form-error">
        {{ formError }}
      </p>
      <form class="app-form" novalidate data-test="form" @submit.prevent="submit">
        <PlaceFields
          v-model="place"
          :errors="Object.fromEntries(Object.entries(fieldErrors).map(([k, v]) => [k, msg(v)]))"
          :disabled="submitting"
          id-prefix="addr"
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
          {{ t('client.addresses.add') }}
        </button>
      </p>

      <ListStatus
        :loading="loading"
        :error="loadError"
        :offline="offline"
        :empty="!loading && !loadError && rows.length === 0"
        :empty-text="t('client.addresses.empty')"
        @retry="load"
      />

      <ul v-if="!loading && !loadError && rows.length" class="addr-list">
        <li v-for="row in rows" :key="row.id" class="addr-row" data-test="row">
          <div>
            <strong>{{ row.name }}</strong>
            <p class="addr-text">{{ row.address }}</p>
          </div>

          <div v-if="confirmingId === row.id" class="form-error" role="alertdialog">
            <p>{{ t('client.addresses.confirmDelete') }}</p>
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
              {{ t('client.addresses.edit') }}
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
.addr-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.addr-row {
  display: grid;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.addr-text {
  margin: 0.25rem 0 0;
}
</style>
