import { defineConfig, devices } from '@playwright/test'
if (!process.env.APP_URL || !process.env.AITRADER_E2E_INSTANCE?.startsWith('e2e-')) {
  throw new Error('Run python scripts/manage.py e2e from the repository root. Browser tests require their own server and database.')
}
export default defineConfig({ testDir: './tests', fullyParallel: false, workers: 1, timeout: 120000, expect: { timeout: 15000 }, use: { baseURL: process.env.APP_URL, trace: 'retain-on-failure', screenshot: 'only-on-failure' }, projects: [{ name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1000 }, channel: 'msedge' } }], reporter: [['list'], ['html', { open: 'never' }]] })
