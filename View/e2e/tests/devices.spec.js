import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('📡 Devices — Quản lý Thiết bị', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/device-management')
        await page.waitForSelector('.page-container, .main-content', { state: 'visible', timeout: 10000 })
    })

    test('8.1 — Trang quản lý thiết bị load thành công', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(10)
    })

    test('8.2 — Hiển thị danh sách cameras / gates', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Trang phải có nội dung dạng bảng hoặc cards
        const container = page.locator('table, .bento-card, .device-card, [class*="card"], [class*="table"]')
        await expect(container.first()).toBeVisible({ timeout: 10000 })
    })
})
