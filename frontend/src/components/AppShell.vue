<script setup>
import { useI18n } from 'vue-i18n'
import { RouterLink, RouterView } from 'vue-router'
import AppHeader from './AppHeader.vue'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
</script>

<template>
  <div class="app-shell">
    <a class="skip-link" href="#main">{{ t('nav.skipToContent') }}</a>
    <AppHeader />
    <main id="main" class="app-content" tabindex="-1">
      <RouterView />
    </main>
    <!-- Only the user's own area (logout lives in the header user menu); anonymous visitors get login and register. -->
    <nav class="bottom-nav" :aria-label="t('nav.bottomNav')">
      <template v-if="auth.isAuthenticated">
        <RouterLink :to="auth.homeRoute" class="bottom-nav-link" active-class="is-active">
          {{ t(`areas.${auth.role === 'manager' ? 'admin' : auth.role}`) }}
        </RouterLink>
      </template>
      <template v-else>
        <RouterLink to="/login" class="bottom-nav-link" active-class="is-active">
          {{ t('nav.login') }}
        </RouterLink>
        <RouterLink to="/register" class="bottom-nav-link" active-class="is-active">
          {{ t('nav.register') }}
        </RouterLink>
      </template>
    </nav>
  </div>
</template>
