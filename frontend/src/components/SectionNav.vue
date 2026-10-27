<script setup>
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

// The one navigation bar used by every area (Admin, Trader, Client, Driver), so it looks and
// behaves the same everywhere (BL-068). items: [{ to, label (i18n key), exact? }].
defineProps({
  label: { type: String, required: true },
  items: { type: Array, required: true },
})
const { t } = useI18n()
</script>

<template>
  <nav class="section-nav" :aria-label="t(label)">
    <RouterLink
      v-for="item in items"
      :key="item.to"
      :to="item.to"
      class="touch-link"
      :exact-active-class="item.exact ? 'is-active' : undefined"
      :active-class="item.exact ? undefined : 'is-active'"
    >
      {{ t(item.label) }}
    </RouterLink>
  </nav>
</template>

<style scoped>
.section-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 1rem;
  margin-block-end: 1rem;
}
.is-active {
  font-weight: 700;
  text-decoration: underline;
}
</style>
