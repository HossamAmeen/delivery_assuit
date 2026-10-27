// PWA settings (installability + app-shell precache only; no offline data features).
export const manifest = {
  name: 'Delivery',
  short_name: 'Delivery',
  description: 'Delivery platform for drivers, traders and clients.',
  start_url: '/',
  scope: '/',
  display: 'standalone',
  theme_color: '#0b5fff',
  background_color: '#f5f7fa',
  lang: 'en',
  dir: 'auto',
  icons: [
    { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
    { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
    {
      src: '/icons/icon-maskable-512.png',
      sizes: '512x512',
      type: 'image/png',
      purpose: 'maskable',
    },
  ],
}

// Never serve these from the service worker (API data must always be live).
export const navigateFallbackDenylist = [/^\/api\//, /^\/admin\//, /^\/static\//, /^\/media\//]

export const workbox = {
  globPatterns: ['**/*.{js,css,html,woff2,png,svg,ico}'],
  navigateFallback: '/index.html',
  navigateFallbackDenylist,
  cleanupOutdatedCaches: true,
  // No runtimeCaching: nothing outside the precached app shell is cached.
  runtimeCaching: [],
}
