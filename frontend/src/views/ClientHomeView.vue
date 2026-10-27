<script setup>
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Client home (BL-044). The order screens arrive in later sprints, so those entries are
// visible but disabled and say so; nothing here is a fake order.
const { t } = useI18n()
const auth = useAuthStore()
</script>

<template>
  <article class="role-home" data-testid="home-client">
    <h1>{{ t('home.client') }}</h1>
    <p class="role-home-user">
      <strong data-testid="home-name">{{ auth.user?.full_name }}</strong>
      <span class="role-badge" data-testid="home-role">{{ t('roles.client') }}</span>
    </p>

    <ul class="entries">
      <li v-for="entry in ['shop', 'direct']" :key="entry">
        <RouterLink
          :to="entry === 'shop' ? '/client/shops' : '/client/direct'"
          class="entry"
          :data-test="`entry-${entry}`"
        >
          <span class="entry-title">{{ t(`clientHome.${entry}`) }}</span>
        </RouterLink>
      </li>
    </ul>

    <nav class="quick" :aria-label="t('clientHome.quickLinks')">
      <RouterLink to="/client/orders" class="btn touch-link" data-test="link-orders">{{
        t('clientHome.myOrders')
      }}</RouterLink>
      <RouterLink to="/client/addresses" class="btn touch-link" data-test="link-addresses">{{
        t('client.nav.addresses')
      }}</RouterLink>
      <RouterLink to="/account/profile" class="btn touch-link" data-test="link-profile">{{
        t('account.profile.menu')
      }}</RouterLink>
    </nav>
  </article>
</template>

<style scoped>
.entries {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  margin-block: 1rem;
  list-style: none;
}
.entry {
  display: grid;
  gap: 0.25rem;
  inline-size: 100%;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-surface);
  color: inherit;
  text-align: start;
}
.entry {
  text-decoration: none;
}
.entry:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.entry-title {
  font-weight: 700;
  font-size: 1.125rem;
}
.entry-note {
  font-size: 0.875rem;
}
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.quick .btn {
  text-decoration: none;
}
</style>
