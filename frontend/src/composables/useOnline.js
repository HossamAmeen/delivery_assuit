import { onBeforeUnmount, onMounted, ref } from 'vue'

// Tracks the browser's online state. It only drives messages and a retry hint:
// a request is never blocked because this says offline.
export function useOnline() {
  const online = ref(typeof navigator === 'undefined' ? true : navigator.onLine !== false)
  const goOnline = () => (online.value = true)
  const goOffline = () => (online.value = false)

  onMounted(() => {
    online.value = navigator.onLine !== false
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
  })
  onBeforeUnmount(() => {
    window.removeEventListener('online', goOnline)
    window.removeEventListener('offline', goOffline)
  })
  return online
}
