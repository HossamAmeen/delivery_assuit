<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()

const areaKey = computed(() => (auth.role === 'manager' ? 'admin' : auth.role))
</script>

<template>
  <article class="role-home" :data-testid="`home-${areaKey}`">
    <h1>{{ t(`home.${areaKey}`) }}</h1>
    <p class="role-home-user">
      <strong data-testid="home-name">{{ auth.user?.full_name }}</strong>
      <span class="role-badge" data-testid="home-role">{{ t(`roles.${auth.role}`) }}</span>
    </p>
    <p class="empty-state" data-testid="home-empty">{{ t('home.empty') }}</p>
  </article>
</template>
