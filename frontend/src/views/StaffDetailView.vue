<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'
import ListStatus from '@/components/ListStatus.vue'
import * as staffApi from '@/api/staff'
import * as usersApi from '@/api/users'
import { ApiError } from '@/api/http'
import { clientError, errorText, formMessage, serverFieldErrors } from '@/utils/forms'

// A driver, trader or client for Admin and Manager (BL-056, BL-057, BL-058, BL-077).
const props = defineProps({
  kind: {
    type: String,
    required: true,
    validator: (v) => ['drivers', 'traders', 'clients'].includes(v),
  },
})
const { t } = useI18n()
const msg = (e) => errorText(e, t)
const route = useRoute()
const id = computed(() => route.params.id)

const data = ref(null)
const loading = ref(true)
const loadError = ref('')
const offline = ref(false)
const missing = ref(false)
const actionError = ref('')
const notice = ref('')
const busy = ref(false)
// Deactivating blocks a person from the app, so it asks first (BL-068).
const confirmingDeactivate = ref(false)
// item id -> price text being edited, and its error
const prices = ref({})
const priceErrors = ref({})

async function load() {
  loading.value = true
  loadError.value = ''
  offline.value = false
  missing.value = false
  try {
    data.value = await staffApi.getStaff(props.kind, id.value)
    prices.value = Object.fromEntries(
      (data.value.items ?? []).map((i) => [i.id, i.price === null ? '' : String(i.price)]),
    )
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) missing.value = true
    else {
      offline.value = Boolean(err?.isNetworkError)
      loadError.value = formMessage(err, t)
    }
  } finally {
    loading.value = false
  }
}
onMounted(load)

const user = computed(() => data.value?.user)

// Approve a pending driver or trader, or activate / deactivate; the Sprint 03 endpoints do the work.
const actions = computed(() => {
  switch (user.value?.status) {
    case 'pending_approval':
      return user.value.role === 'client' ? [] : [['approve', usersApi.approveUser]]
    case 'active':
      return [['deactivate', usersApi.deactivateUser]]
    case 'deactivated':
      return [['activate', usersApi.activateUser]]
    default:
      return []
  }
})

async function act(call) {
  if (busy.value) return
  confirmingDeactivate.value = false
  busy.value = true
  actionError.value = ''
  notice.value = ''
  try {
    const updated = await call(user.value.id)
    data.value = { ...data.value, user: { ...data.value.user, status: updated.status } }
    notice.value = t('admin.staff.updated')
  } catch (err) {
    actionError.value = formMessage(err, t)
  } finally {
    busy.value = false
  }
}

const deactivateAccount = () => act(usersApi.deactivateUser)

async function savePrice(item) {
  if (busy.value) return
  actionError.value = ''
  notice.value = ''
  const text = (prices.value[item.id] ?? '').trim()
  let price = null
  if (text !== '') {
    price = Number(text)
    if (!Number.isFinite(price) || price < 0 || price > 100000 || !/^\d+(\.\d{1,2})?$/.test(text)) {
      priceErrors.value = {
        ...priceErrors.value,
        [item.id]: clientError('admin.staff.priceInvalid'),
      }
      return
    }
  }
  priceErrors.value = { ...priceErrors.value, [item.id]: null }
  busy.value = true
  try {
    const saved = await staffApi.setItemPrice(item.id, price)
    data.value.items = data.value.items.map((i) =>
      i.id === item.id ? { ...i, price: saved.price } : i,
    )
    notice.value = t('admin.staff.priceSaved')
  } catch (err) {
    const f = serverFieldErrors(err, ['price'])
    if (f.price) priceErrors.value = { ...priceErrors.value, [item.id]: f.price }
    else actionError.value = formMessage(err, t)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <p>
      <RouterLink :to="`/admin/${kind}`" class="touch-link">{{
        t(`admin.staff.${kind}.title`)
      }}</RouterLink>
    </p>

    <ListStatus :loading="loading" :error="loadError" :offline="offline" @retry="load" />
    <div v-if="missing" class="form-notice" role="status" data-test="missing">
      {{ t('admin.staff.notFound') }}
    </div>

    <template v-if="data && !loading">
      <h1 data-test="name">{{ user.full_name }}</h1>
      <p v-if="notice" class="form-notice" role="status" data-test="notice">{{ notice }}</p>
      <p v-if="actionError" class="form-error" role="alert" data-test="action-error">
        {{ actionError }}
      </p>

      <dl class="details">
        <div>
          <dt>{{ t('admin.staff.phone') }}</dt>
          <dd dir="ltr" data-test="phone">{{ user.phone }}</dd>
        </div>
        <div v-if="user.email">
          <dt>{{ t('account.profile.email') }}</dt>
          <dd dir="ltr">{{ user.email }}</dd>
        </div>
        <div>
          <dt>{{ t('admin.users.status') }}</dt>
          <dd data-test="status">{{ t(`statuses.${user.status}`) }}</dd>
        </div>
        <div>
          <dt>{{ t('admin.staff.ordersTotal') }}</dt>
          <dd data-test="orders-total">{{ data.orders_total }}</dd>
        </div>
        <template v-if="kind === 'drivers'">
          <div>
            <dt>{{ t('admin.staff.drivers.count') }}</dt>
            <dd data-test="delivered">{{ data.delivered_orders }}</dd>
          </div>
          <div>
            <dt>{{ t('admin.staff.cancelled') }}</dt>
            <dd data-test="cancelled">{{ data.cancelled_orders }}</dd>
          </div>
          <div v-if="data.active_order_reference">
            <dt>{{ t('admin.staff.activeOrder') }}</dt>
            <dd dir="ltr" data-test="active-order">{{ data.active_order_reference }}</dd>
          </div>
        </template>
      </dl>

      <div
        v-if="confirmingDeactivate"
        class="form-error"
        role="alertdialog"
        data-test="confirm-box"
      >
        <p>{{ t('admin.users.confirmDeactivate') }}</p>
        <div class="btn-row">
          <button
            type="button"
            class="btn btn-danger"
            data-test="confirm-deactivate"
            :disabled="busy"
            @click="deactivateAccount"
          >
            {{ t('admin.userForm.confirmYes') }}
          </button>
          <button type="button" class="btn" data-test="keep" @click="confirmingDeactivate = false">
            {{ t('common.cancel') }}
          </button>
        </div>
      </div>
      <div v-else-if="actions.length" class="btn-row">
        <button
          v-for="[name, call] in actions"
          :key="name"
          type="button"
          :class="['btn', name === 'deactivate' ? 'btn-danger' : 'btn-primary']"
          :data-test="name"
          :disabled="busy"
          @click="name === 'deactivate' ? (confirmingDeactivate = true) : act(call)"
        >
          {{ t(`admin.staff.actions.${name}`) }}
        </button>
      </div>

      <template v-if="kind === 'traders'">
        <h2>{{ t('admin.staff.shop') }}</h2>
        <p v-if="!data.shop" data-test="no-shop">{{ t('admin.staff.noShop') }}</p>
        <p v-else data-test="shop">
          {{ data.shop.name }} —
          {{ data.shop.is_available ? t('admin.staff.open') : t('admin.staff.closed') }}
        </p>

        <h2>{{ t('trader.nav.locations') }}</h2>
        <ul class="plain">
          <li v-for="l in data.locations" :key="l.id" data-test="location">
            {{ l.name }} — {{ l.address }}
          </li>
        </ul>

        <h2>{{ t('trader.nav.items') }}</h2>
        <p v-if="data.items.length === 0" data-test="no-items">{{ t('shop.items.empty') }}</p>
        <ul class="plain">
          <li v-for="item in data.items" :key="item.id" class="item" data-test="item">
            <div>
              <strong>{{ item.name }}</strong>
              <span v-if="item.is_hidden" class="role-badge">{{
                t('shop.items.hiddenBadge')
              }}</span>
            </div>
            <div class="price-row">
              <label :for="`price-${item.id}`">{{ t('admin.staff.price') }}</label>
              <input
                :id="`price-${item.id}`"
                v-model="prices[item.id]"
                type="text"
                inputmode="decimal"
                dir="ltr"
                :disabled="busy"
                :aria-invalid="priceErrors[item.id] ? 'true' : 'false'"
                :data-test="`price-${item.id}`"
              />
              <button
                type="button"
                class="btn"
                :data-test="`save-price-${item.id}`"
                :disabled="busy"
                @click="savePrice(item)"
              >
                {{ t('account.profile.save') }}
              </button>
            </div>
            <p v-if="priceErrors[item.id]" class="field-error" role="alert" data-test="price-error">
              {{ msg(priceErrors[item.id]) }}
            </p>
          </li>
        </ul>
      </template>

      <h2>{{ t('admin.staff.recent') }}</h2>
      <p v-if="data.recent_orders.length === 0" data-test="no-orders">
        {{ t('admin.staff.noOrders') }}
      </p>
      <ul class="plain">
        <li v-for="o in data.recent_orders" :key="o.id" data-test="order">
          <RouterLink :to="`/admin/orders/${o.id}`" dir="ltr">{{ o.reference }}</RouterLink>
          — {{ t(`orders.status.${o.status}`) }}
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.details {
  display: grid;
  gap: 0.75rem;
  margin: 1rem 0;
}
.details div {
  display: grid;
  gap: 0.125rem;
}
dt {
  font-weight: 600;
}
dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.plain {
  display: grid;
  gap: 0.5rem;
  padding: 0;
  list-style: none;
}
.item {
  display: grid;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
}
.price-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
label {
  font-weight: 600;
}
input {
  font: inherit;
  inline-size: 7rem;
  min-block-size: var(--touch-target);
  padding-inline: 0.75rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.25rem;
}
.field-error {
  margin: 0;
  color: #b42318;
  font-size: 0.875rem;
}
</style>
