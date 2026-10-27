<script setup>
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

const { t } = useI18n()
const roles = ['client', 'driver', 'trader']
</script>

<template>
  <section class="auth-page">
    <h1>{{ t('auth.pages.register') }}</h1>
    <p>{{ t('auth.register.chooseIntro') }}</p>
    <ul class="role-list">
      <li v-for="role in roles" :key="role">
        <RouterLink :to="`/register/${role}`" class="role-card" :data-test="`choose-${role}`">
          <strong>{{ t(`auth.register.roles.${role}.title`) }}</strong>
          <span>{{ t(`auth.register.roles.${role}.desc`) }}</span>
        </RouterLink>
      </li>
    </ul>
    <p class="auth-switch">
      {{ t('auth.register.haveAccount') }}
      <RouterLink to="/login" class="touch-link">{{ t('nav.login') }}</RouterLink>
    </p>
  </section>
</template>

<style scoped>
.auth-page {
  max-inline-size: 28rem;
  margin-inline: auto;
}
.role-list {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  list-style: none;
}
.role-card {
  display: grid;
  gap: 0.25rem;
  min-block-size: var(--touch-target);
  padding: 0.75rem 1rem;
  border: 1px solid #9aa5b1;
  border-radius: 0.5rem;
  background: var(--color-surface);
  color: inherit;
  text-decoration: none;
}
.role-card span {
  font-size: 0.875rem;
  color: #52606d;
}
.auth-switch {
  margin-block-start: 1.5rem;
}
</style>
