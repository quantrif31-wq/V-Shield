import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('🚗 Vehicles — Quản lý Phương tiện', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/vehicles')
        await page.waitForSelector('.page-container', { state: 'visible', timeout: 10000 })
    })

    test('4.1 — Trang phương tiện load và hiển thị bảng', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Kiểm tra header
        await expect(page.locator('h1.page-title')).toContainText('Quản lý Phương tiện')

        // Kiểm tra stats cards
        const statCards = page.locator('.stat-card')
        await expect(statCards.first()).toBeVisible({ timeout: 10000 })

        // Kiểm tra bảng hoặc empty state
        const tableOrEmpty = page.locator('.sleek-table, .empty-layout')
        await expect(tableOrEmpty.first()).toBeVisible({ timeout: 10000 })
    })

    test('4.2 — Mở form đăng ký phương tiện', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Click nút thêm
        const addBtn = page.locator('button').filter({ hasText: 'Đăng ký phương tiện' })
        await expect(addBtn).toBeVisible()
        await addBtn.click()

        // Kiểm tra modal
        await expect(page.locator('.modern-modal')).toBeVisible({ timeout: 5000 })
        await expect(page.locator('.modal-top h3')).toContainText('Đăng ký Phương tiện')

        // Kiểm tra field biển số
        await expect(page.locator('.modern-modal input[placeholder*="51A"]')).toBeVisible()
    })

    test('4.3 — Tìm kiếm phương tiện', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const searchInput = page.locator('.search-box input')
        await expect(searchInput).toBeVisible()
        await searchInput.fill('51A')
        
        await page.waitForTimeout(1000)
        
        const tableOrEmpty = page.locator('.sleek-table, .empty-layout')
        await expect(tableOrEmpty.first()).toBeVisible()
    })

    test('4.4 — Hiển thị thống kê phương tiện', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Kiểm tra 3 stat cards hiển thị
        const statCards = page.locator('.stat-card')
        const count = await statCards.count()
        expect(count).toBeGreaterThanOrEqual(3)
    })
})
