import { onBeforeUnmount, onMounted } from 'vue'

// Calls `refresh` on an interval and when the tab becomes visible again (BL-067).
// It skips while the tab is hidden or the browser is offline, never overlaps two calls, and
// swallows errors: the screen's own load already shows them, and a quiet refresh must not
// replace what the user is looking at with an error.
export function useAutoRefresh(refresh, { interval = 30000 } = {}) {
  let timer = null
  let running = false

  async function tick() {
    if (running) return
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return
    running = true
    try {
      await refresh()
    } catch {
      // keep what is on screen
    } finally {
      running = false
    }
  }

  const onVisible = () => {
    if (document.visibilityState === 'visible') tick()
  }

  onMounted(() => {
    timer = setInterval(tick, interval)
    document.addEventListener('visibilitychange', onVisible)
  })
  onBeforeUnmount(() => {
    clearInterval(timer)
    document.removeEventListener('visibilitychange', onVisible)
  })
  return { tick }
}
