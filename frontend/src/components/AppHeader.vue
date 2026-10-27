<script setup>
import { ref, nextTick, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'
import LanguageSwitcher from './LanguageSwitcher.vue'
import NotificationBell from './NotificationBell.vue'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()

const open = ref(false)
const root = ref(null)
const trigger = ref(null)

function onDocClick(e) {
  if (root.value && !root.value.contains(e.target)) open.value = false
}
watch(open, (v) => {
  if (v) document.addEventListener('click', onDocClick)
  else document.removeEventListener('click', onDocClick)
})
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))

function onKeydown(e) {
  if (e.key === 'Escape' && open.value) {
    open.value = false
    nextTick(() => trigger.value?.focus())
  }
}

// Clears the local session first (even if the API call fails), then goes to login.
async function logout() {
  open.value = false
  try {
    await auth.logout()
  } finally {
    router.replace({ name: 'login' })
  }
}
</script>

<template>
  <header class="app-header">
    <span class="brand">{{ t('app.name') }}</span>
    <div class="header-actions">
      <LanguageSwitcher />
      <NotificationBell v-if="auth.isAuthenticated" />
      <div v-if="auth.isAuthenticated" ref="root" class="user-menu" @keydown="onKeydown">
        <button
          ref="trigger"
          type="button"
          class="user-menu-button"
          aria-haspopup="true"
          :aria-expanded="open"
          aria-controls="user-menu-panel"
          :aria-label="`${t('userMenu.button')}: ${auth.user.full_name}`"
          data-testid="user-menu-button"
          @click="open = !open"
        >
          <span class="user-menu-name">{{ auth.user.full_name }}</span>
        </button>
        <div v-if="open" id="user-menu-panel" class="user-menu-panel" data-testid="user-menu-panel">
          <p class="user-menu-info">
            <strong>{{ auth.user.full_name }}</strong>
            <span>{{ t(`roles.${auth.role}`) }}</span>
          </p>
          <RouterLink
            :to="{ name: 'profile' }"
            class="user-menu-link"
            data-testid="menu-profile"
            @click="open = false"
          >
            {{ t('account.profile.menu') }}
          </RouterLink>
          <RouterLink
            :to="{ name: 'change-password' }"
            class="user-menu-link"
            data-testid="menu-password"
            @click="open = false"
          >
            {{ t('account.password.menu') }}
          </RouterLink>
          <button type="button" class="user-menu-logout" data-testid="logout" @click="logout">
            {{ t('nav.logout') }}
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
