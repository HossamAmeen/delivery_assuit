<script setup>
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import HealthStatus from '@/components/HealthStatus.vue'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()

const auth = useAuthStore()

// Developer aid only. Production health is checked from the server side (curl, tests, monitoring):
// a browser cannot hold the health password, so the widget is not shown or called in production.
const showHealth = import.meta.env.DEV
</script>

<template>
  <section>
    <h1>{{ t('app.name') }}</h1>
    <nav :aria-label="t('nav.areas')">
      <ul>
        <template v-if="auth.isAuthenticated">
          <li>
            <RouterLink :to="auth.homeRoute">{{
              t(`areas.${auth.role === 'manager' ? 'admin' : auth.role}`)
            }}</RouterLink>
          </li>
        </template>
        <template v-else>
          <li>
            <RouterLink to="/login">{{ t('nav.login') }}</RouterLink>
          </li>
          <li>
            <RouterLink to="/register">{{ t('nav.register') }}</RouterLink>
          </li>
        </template>
      </ul>
    </nav>
    <HealthStatus v-if="showHealth" />
  </section>
</template>
