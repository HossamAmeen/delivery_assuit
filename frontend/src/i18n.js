import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import ar from './locales/ar.json'

export const SUPPORTED_LOCALES = ['en', 'ar']
export const DEFAULT_LOCALE = 'en'

// Every locale file is picked up here; a new key only needs to be added to the JSON files.
export const i18n = createI18n({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: DEFAULT_LOCALE,
  messages: { en, ar },
})

export default i18n
