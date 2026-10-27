import { defineStore } from 'pinia'
import { i18n, SUPPORTED_LOCALES, DEFAULT_LOCALE } from '@/i18n'

export const STORAGE_KEY = 'locale'

function readStored() {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return SUPPORTED_LOCALES.includes(value) ? value : null
  } catch {
    return null
  }
}

function writeStored(locale) {
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // Storage can be blocked (private mode); the choice then lasts for this session only.
  }
}

export const useLanguageStore = defineStore('language', {
  state: () => ({ locale: DEFAULT_LOCALE }),
  getters: {
    dir: (state) => (state.locale === 'ar' ? 'rtl' : 'ltr'),
  },
  actions: {
    apply() {
      i18n.global.locale.value = this.locale
      document.documentElement.lang = this.locale
      document.documentElement.dir = this.dir
    },
    init() {
      this.locale = readStored() ?? DEFAULT_LOCALE
      this.apply()
    },
    setLocale(locale) {
      if (!SUPPORTED_LOCALES.includes(locale)) return
      this.locale = locale
      this.apply()
      writeStored(locale)
    },
  },
})
