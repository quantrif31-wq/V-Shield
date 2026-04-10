import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('📋 Access Logs — Nhật ký ra vào', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/access-logs')
        await page.waitForSelector('.page-container, .main-content', { state: 'visible', timeout: 10000 })
    })

    test('7.1 — Trang nhật ký ra vào load thành công', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Kiểm tra trang có nội dung
        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(10)
    })

    test('7.2 — Hiển thị bảng hoặc empty state', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Bảng dữ liệu hoặc empty state
        const tableOrEmpty = page.locator('table, .empty-layout, .empty-state, [class*="table"]')
        await expect(tableOrEmpty.first()).toBeVisible({ timeout: 10000 })
    })
})
