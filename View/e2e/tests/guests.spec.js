import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('🧑‍💼 Guest Profiles — Hồ sơ Khách', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/guest-profiles')
        await page.waitForSelector('.page-container, .main-content', { state: 'visible', timeout: 10000 })
    })

    test('11.1 — Trang hồ sơ khách load thành công', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(10)
    })

    test('11.2 — Hiển thị bảng hoặc empty state', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const tableOrEmpty = page.locator('table, .empty-layout, .bento-card, [class*="table"]')
        await expect(tableOrEmpty.first()).toBeVisible({ timeout: 10000 })
    })
})
