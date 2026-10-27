import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { useLanguageStore } from './stores/language'
import { useAuthStore } from './stores/auth'
import './assets/main.css'
import { registerSW } from 'virtual:pwa-register'

const app = createApp(App).use(createPinia()).use(router).use(i18n)
useLanguageStore().init()
// Session end -> login; a 403 role refusal -> the user's own area.
const auth = useAuthStore()
auth.init({
  onSessionEnded: () => router.replace({ name: 'login' }),
  onForbidden: () => {
    if (auth.isAuthenticated && router.currentRoute.value.fullPath !== auth.homeRoute) {
      router.replace(auth.homeRoute)
    }
  },
})
auth.ensureRestored()
app.mount('#app')

// Production only: the service worker is not registered during `npm run dev`.
if (import.meta.env.PROD) registerSW({ immediate: true })
