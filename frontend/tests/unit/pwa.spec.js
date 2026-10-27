import { describe, it, expect } from 'vitest'
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { manifest, workbox, navigateFallbackDenylist } from '../../pwa.config.js'

describe('PWA manifest', () => {
  it('is installable: name, standalone, start_url, colors', () => {
    expect(manifest.name).toBeTruthy()
    expect(manifest.short_name).toBeTruthy()
    expect(manifest.display).toBe('standalone')
    expect(manifest.start_url).toBe('/')
    expect(manifest.theme_color).toMatch(/^#[0-9a-f]{6}$/i)
    expect(manifest.background_color).toMatch(/^#[0-9a-f]{6}$/i)
    expect(manifest.lang).toBe('en')
    expect(manifest.dir).toBe('auto')
  })

  it('has 192, 512 and maskable icons that exist on disk', () => {
    const find = (sizes, purpose) =>
      manifest.icons.find((i) => i.sizes === sizes && i.purpose === purpose)
    expect(find('192x192', 'any')).toBeTruthy()
    expect(find('512x512', 'any')).toBeTruthy()
    expect(find('512x512', 'maskable')).toBeTruthy()
    for (const icon of manifest.icons) {
      expect(existsSync(resolve('public', icon.src.slice(1)))).toBe(true)
    }
  })
})

describe('service worker config', () => {
  it('never caches API responses', () => {
    expect(workbox.runtimeCaching).toEqual([])
    expect(navigateFallbackDenylist.some((re) => re.test('/api/v1/health/'))).toBe(true)
    expect(workbox.navigateFallbackDenylist).toBe(navigateFallbackDenylist)
  })

  it('does not route the admin site to the app shell', () => {
    expect(navigateFallbackDenylist.some((re) => re.test('/admin/login/'))).toBe(true)
  })
})
