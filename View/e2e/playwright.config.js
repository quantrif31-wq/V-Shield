// @ts-check
import { defineConfig } from '@playwright/test'

export default defineConfig({
    testDir: './tests',
    timeout: 30000,
    expect: { timeout: 10000 },
    fullyParallel: false,
    retries: 0,
    workers: 1,
    reporter: [
        ['list'],
        ['html', { outputFolder: '../playwright-report', open: 'never' }],
    ],
    use: {
        baseURL: 'http://localhost:5173',
        headless: true,
        viewport: { width: 1280, height: 800 },
        actionTimeout: 10000,
        navigationTimeout: 15000,
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        trace: 'retain-on-failure',
    },
    projects: [
        {
            name: 'chromium',
            use: { browserName: 'chromium' },
        },
    ],
})
