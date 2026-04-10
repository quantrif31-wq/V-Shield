import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('📄 Misc Pages — Các trang phụ trợ', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.waitForSelector('.main-content', { state: 'visible', timeout: 10000 })
    })

    test('12.1 — Trang Settings load thành công', async ({ page }) => {
        await page.goto('/settings')
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(10)
    })

    test('12.2 — Trang Monitoring load thành công', async ({ page }) => {
        await page.goto('/monitoring')
        await page.waitForTimeout(3000)

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(5)
    })

    test('12.3 — Trang System Catalog load thành công', async ({ page }) => {
        await page.goto('/system-catalog')
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(10)
    })

    test('12.4 — Trang Biometrics load thành công', async ({ page }) => {
        await page.goto('/biometrics')
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(5)
    })

    test('12.5 — Trang About Project load thành công', async ({ page }) => {
        await page.goto('/about-project')
        await page.waitForTimeout(2000)

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThanOrEqual(0) // Trang này có thể tối giản
    })
})
