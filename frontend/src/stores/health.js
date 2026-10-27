import { defineStore } from 'pinia'
import { getHealth } from '@/api/health'

export const useHealthStore = defineStore('health', {
  state: () => ({
    // 'idle' | 'loading' | 'healthy' | 'error'
    status: 'idle',
    error: null,
  }),
  actions: {
    async check() {
      this.status = 'loading'
      this.error = null
      try {
        const data = await getHealth()
        this.status = data?.status === 'healthy' ? 'healthy' : 'error'
        if (this.status === 'error') this.error = { status: 0, isNetworkError: false, message: '' }
      } catch (err) {
        this.status = 'error'
        this.error = {
          status: err.status ?? 0,
          isNetworkError: Boolean(err.isNetworkError),
          message: err.message ?? '',
        }
      }
    },
  },
})
