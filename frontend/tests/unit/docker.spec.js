import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'

// Docker is not run by agents (PO decision 2026-10-08); these check the files by reading them.
const dockerfile = readFileSync('Dockerfile', 'utf8')
const ignore = readFileSync('.dockerignore', 'utf8').split('\n')

describe('frontend Dockerfile', () => {
  it('installs from the lockfile and runs the dev server on 0.0.0.0:5173', () => {
    expect(dockerfile).toContain('npm ci')
    expect(dockerfile).toContain('package-lock.json')
    expect(dockerfile).toContain('EXPOSE 5173')
    expect(dockerfile).toMatch(/CMD \[.*"--host", "0\.0\.0\.0".*"--port", "5173"\]/)
  })

  it('runs as a non-root user', () => {
    expect(dockerfile).toMatch(/^USER node$/m)
  })

  it('bakes in no environment files or secrets', () => {
    expect(dockerfile).not.toMatch(/COPY\s+\.env|ADD\s+\.env/)
    expect(dockerfile).not.toMatch(/(TOKEN|PASSWORD|SECRET)\s*=/)
  })

  it('.dockerignore excludes node_modules and env files', () => {
    for (const entry of ['node_modules', '.env', '.env.*', 'dist']) {
      expect(ignore).toContain(entry)
    }
  })
})
