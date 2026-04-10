import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('📝 Pre-Registration — Đăng ký trước', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/pre-registrations')
        await page.waitForSelector('.page-container, .main-content', { state: 'visible', timeout: 10000 })
    })

    test('9.1 — Trang đăng ký trước load thành công', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(10)
    })

    test('9.2 — Hiển thị bảng hoặc empty state', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const tableOrEmpty = page.locator('table, .empty-layout, .bento-card, [class*="table"]')
        await expect(tableOrEmpty.first()).toBeVisible({ timeout: 10000 })
    })
})

test.describe('🔗 Registration Links — Link đăng ký', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/registration-links')
        await page.waitForSelector('.page-container, .main-content', { state: 'visible', timeout: 10000 })
    })

    test('9.3 — Trang link đăng ký load thành công', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const content = await page.locator('.page-container, .main-content').first().innerText()
        expect(content.length).toBeGreaterThan(10)
    })
})
