<script setup>
import { useI18n } from 'vue-i18n'
import { SUPPORTED_LOCALES } from '@/i18n'
import { useLanguageStore } from '@/stores/language'

const { t } = useI18n()
const language = useLanguageStore()
</script>

<template>
  <div class="language-switcher" role="group" :aria-label="t('language.label')">
    <button
      v-for="code in SUPPORTED_LOCALES"
      :key="code"
      type="button"
      :lang="code"
      :aria-pressed="language.locale === code"
      :data-locale="code"
      @click="language.setLocale(code)"
    >
      {{ t(`language.${code}`) }}
    </button>
  </div>
</template>
