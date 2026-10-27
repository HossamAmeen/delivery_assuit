import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { i18n } from '@/i18n'
import { useLanguageStore, STORAGE_KEY } from '@/stores/language'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import en from '@/locales/en.json'
import ar from '@/locales/ar.json'

function keys(obj, prefix = '') {
  return Object.entries(obj).flatMap(([k, v]) =>
    typeof v === 'object' ? keys(v, `${prefix}${k}.`) : [`${prefix}${k}`],
  )
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
  i18n.global.locale.value = 'en'
  document.documentElement.lang = ''
  document.documentElement.dir = ''
})

describe('language store', () => {
  it('defaults to English / ltr', () => {
    const store = useLanguageStore()
    store.init()
    expect(store.locale).toBe('en')
    expect(document.documentElement.lang).toBe('en')
    expect(document.documentElement.dir).toBe('ltr')
  })

  it('switches to Arabic: sets lang, dir, i18n locale and persists', () => {
    const store = useLanguageStore()
    store.init()
    store.setLocale('ar')
    expect(document.documentElement.lang).toBe('ar')
    expect(document.documentElement.dir).toBe('rtl')
    expect(i18n.global.locale.value).toBe('ar')
    expect(localStorage.getItem(STORAGE_KEY)).toBe('ar')
  })

  it('restores the saved choice (survives refresh)', () => {
    localStorage.setItem(STORAGE_KEY, 'ar')
    const store = useLanguageStore()
    store.init()
    expect(store.locale).toBe('ar')
    expect(document.documentElement.dir).toBe('rtl')
  })

  it('ignores unsupported stored or requested locales', () => {
    localStorage.setItem(STORAGE_KEY, 'fr')
    const store = useLanguageStore()
    store.init()
    expect(store.locale).toBe('en')
    store.setLocale('fr')
    expect(store.locale).toBe('en')
  })

  it('still works when localStorage throws', () => {
    const get = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    const set = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    const store = useLanguageStore()
    store.init()
    store.setLocale('ar')
    expect(store.locale).toBe('ar')
    expect(document.documentElement.dir).toBe('rtl')
    get.mockRestore()
    set.mockRestore()
  })
})

describe('LanguageSwitcher', () => {
  it('flips text and direction without reload', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const wrapper = mount(LanguageSwitcher, { global: { plugins: [pinia, i18n] } })
    expect(wrapper.find('[role="group"]').attributes('aria-label')).toBe('Language')
    expect(wrapper.find('[data-locale="en"]').attributes('aria-pressed')).toBe('true')
    await wrapper.find('[data-locale="ar"]').trigger('click')
    await nextTick()
    expect(wrapper.find('[role="group"]').attributes('aria-label')).toBe(ar.language.label)
    expect(wrapper.find('[data-locale="ar"]').attributes('aria-pressed')).toBe('true')
    expect(document.documentElement.dir).toBe('rtl')
    await wrapper.find('[data-locale="en"]').trigger('click')
    expect(document.documentElement.dir).toBe('ltr')
  })
})

describe('locale files', () => {
  it('have identical keys in en and ar', () => {
    expect(keys(ar).sort()).toEqual(keys(en).sort())
  })
})
