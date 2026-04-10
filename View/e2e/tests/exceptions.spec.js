import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('⚠️ Exceptions — Ngoại lệ', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/exceptions')
        await page.waitForSelector('.page-container, .main-content', { state: 'visible', timeout: 10000 })
    })

    test('10.1 — Trang ngoại lệ load thành công', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(10)
    })

    test('10.2 — Hiển thị bảng ngoại lệ hoặc empty state', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const tableOrEmpty = page.locator('table, .empty-layout, .bento-card, [class*="table"]')
        await expect(tableOrEmpty.first()).toBeVisible({ timeout: 10000 })
    })
})
