<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ListStatus from '@/components/ListStatus.vue'
import PlaceFields from '@/components/PlaceFields.vue'
import * as locationsApi from '@/api/locations'
import { clientError, errorText, formMessage, serverFieldErrors } from '@/utils/forms'
import { emptyPlace, placePayload, placeProblems, placeToForm } from '@/utils/places'

const { t } = useI18n()
const msg = (e) => errorText(e, t)

const rows = ref([])
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const pageError = ref('')

// The form is closed (null), a new location ('new'), or the id being edited.
const editing = ref(null)
const place = ref(emptyPlace())
const isPickup = ref(true)
const isDelivery = ref(false)
const isDefault = ref(false)
const fieldErrors = ref({})
const formError = ref('')
const submitting = ref(false)
const confirmingId = ref(null)
const busyId = ref(null)

const FIELDS = [
  'name',
  'address',
  'latitude',
  'longitude',
  'is_pickup',
  'is_delivery',
  'is_default_pickup',
]

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  try {
    rows.value = (await locationsApi.listLocations({ page_size: 100 })).results
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
  isPickup.value = row ? row.is_pickup : true
  isDelivery.value = row ? row.is_delivery : false
  isDefault.value = row ? row.is_default_pickup : false
  fieldErrors.value = {}
  formError.value = ''
}

function closeForm() {
  editing.value = null
}

function validate() {
  const errors = placeProblems(place.value)
  if (!isPickup.value && !isDelivery.value) errors.is_pickup = clientError('places.errors.needOne')
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

async function submit() {
  if (submitting.value) return
  formError.value = ''
  if (!validate()) return
  submitting.value = true
  const body = {
    ...placePayload(place.value),
    is_pickup: isPickup.value,
    is_delivery: isDelivery.value,
    is_default_pickup: isPickup.value && isDefault.value,
  }
  try {
    if (editing.value === 'new') await locationsApi.createLocation(body)
    else await locationsApi.updateLocation(editing.value, body)
    closeForm()
    // The default may have moved on other rows, so reload rather than patching one row.
    await load()
  } catch (err) {
    fieldErrors.value = serverFieldErrors(err, FIELDS)
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
    await locationsApi.deleteLocation(id)
    confirmingId.value = null
    await load()
  } catch (err) {
    confirmingId.value = null
    pageError.value = formMessage(err, t)
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <section class="form-page locations">
    <h1>{{ t('trader.locations.title') }}</h1>
    <p>{{ t('trader.locations.intro') }}</p>
    <p v-if="pageError" class="form-error" role="alert" data-test="page-error">{{ pageError }}</p>

    <div v-if="editing !== null">
      <h2 data-test="form-title">
        {{ editing === 'new' ? t('trader.locations.add') : t('trader.locations.edit') }}
      </h2>
      <p v-if="formError" class="form-error" role="alert" data-test="form-error">
        {{ formError }}
      </p>
      <form class="app-form" novalidate data-test="form" @submit.prevent="submit">
        <PlaceFields
          v-model="place"
          :errors="Object.fromEntries(Object.entries(fieldErrors).map(([k, v]) => [k, msg(v)]))"
          :disabled="submitting"
          id-prefix="loc"
        />
        <fieldset class="flags">
          <legend>{{ t('trader.locations.usedFor') }}</legend>
          <label class="check">
            <input
              v-model="isPickup"
              type="checkbox"
              data-test="is-pickup"
              :disabled="submitting"
            />
            {{ t('trader.locations.pickup') }}
          </label>
          <label class="check">
            <input
              v-model="isDelivery"
              type="checkbox"
              data-test="is-delivery"
              :disabled="submitting"
            />
            {{ t('trader.locations.delivery') }}
          </label>
          <p v-if="fieldErrors.is_pickup" class="field-error" role="alert" data-test="flags-error">
            {{ msg(fieldErrors.is_pickup) }}
          </p>
          <label class="check">
            <input
              v-model="isDefault"
              type="checkbox"
              data-test="is-default"
              :disabled="submitting || !isPickup"
            />
            {{ t('trader.locations.makeDefault') }}
          </label>
          <p v-if="fieldErrors.is_default_pickup" class="field-error" role="alert">
            {{ msg(fieldErrors.is_default_pickup) }}
          </p>
        </fieldset>
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
          <button type="button" class="btn" data-test="cancel" @click="closeForm">
            {{ t('common.cancel') }}
          </button>
        </div>
      </form>
    </div>

    <template v-else>
      <p>
        <button type="button" class="btn btn-primary" data-test="add" @click="openForm(null)">
          {{ t('trader.locations.add') }}
        </button>
      </p>

      <ListStatus
        :loading="loading"
        :error="loadError"
        :offline="offline"
        :empty="!loading && !loadError && rows.length === 0"
        :empty-text="t('trader.locations.empty')"
        @retry="load"
      />

      <ul v-if="!loading && !loadError && rows.length" class="loc-list">
        <li v-for="row in rows" :key="row.id" class="loc-row" data-test="row">
          <div>
            <strong>{{ row.name }}</strong>
            <span v-if="row.is_default_pickup" class="role-badge" data-test="badge-default">{{
              t('trader.locations.defaultBadge')
            }}</span>
            <span v-if="row.is_pickup" class="role-badge" data-test="badge-pickup">{{
              t('trader.locations.pickup')
            }}</span>
            <span v-if="row.is_delivery" class="role-badge" data-test="badge-delivery">{{
              t('trader.locations.delivery')
            }}</span>
            <p class="loc-address">{{ row.address }}</p>
          </div>

          <div v-if="confirmingId === row.id" class="form-error" role="alertdialog">
            <p>{{ t('trader.locations.confirmDelete') }}</p>
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
              {{ t('trader.locations.edit') }}
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
.loc-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.loc-row {
  display: grid;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.loc-address {
  margin: 0.25rem 0 0;
}
.flags {
  display: grid;
  gap: 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
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
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
</style>
