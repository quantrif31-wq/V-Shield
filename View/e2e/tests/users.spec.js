import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('👤 Users — Quản lý Tài khoản', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/users')
        await page.waitForSelector('.page-container', { state: 'visible', timeout: 10000 })
    })

    test('5.1 — Trang tài khoản load và hiển thị bảng', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        await expect(page.locator('h1.page-title')).toContainText('Quản lý Tài khoản')

        // Kiểm tra có ít nhất 1 user (admin)
        const tableRows = page.locator('.sleek-table tbody .table-row')
        await expect(tableRows.first()).toBeVisible({ timeout: 10000 })
    })

    test('5.2 — Mở form thêm tài khoản mới', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const addBtn = page.locator('button').filter({ hasText: 'Thêm tài khoản' })
        await expect(addBtn).toBeVisible()
        await addBtn.click()

        await expect(page.locator('.modern-modal')).toBeVisible({ timeout: 5000 })
        await expect(page.locator('.modal-top h3')).toContainText('Thêm Tài khoản')

        // Kiểm tra có fields username, password, role
        await expect(page.locator('.modern-modal input[placeholder*="Nhập tên đăng nhập"]')).toBeVisible()
        await expect(page.locator('.modern-modal input[type="password"]')).toBeVisible()
        await expect(page.locator('.modern-modal select.sleek-select')).toBeVisible()
    })

    test('5.3 — Tạo tài khoản mới thành công', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        await page.locator('button').filter({ hasText: 'Thêm tài khoản' }).click()
        await expect(page.locator('.modern-modal')).toBeVisible({ timeout: 5000 })

        const uniqueUser = `autotest_${Date.now().toString().slice(-6)}`
        await page.locator('.modern-modal input[placeholder*="Nhập tên đăng nhập"]').fill(uniqueUser)
        await page.locator('.modern-modal input[type="password"]').fill('Test@12345')
        await page.locator('.modern-modal select.sleek-select').first().selectOption('Staff')

        await page.locator('.modern-modal button[type="submit"]').click()
        await expect(page.locator('.modern-modal')).toBeHidden({ timeout: 10000 })
    })

    test('5.4 — Filter tài khoản theo vai trò', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Filter theo Admin
        const roleFilter = page.locator('select.minimal-select').first()
        await roleFilter.selectOption('Admin')
        
        await page.waitForTimeout(500)

        // Kiểm tra bảng vẫn hiển thị
        const tableOrEmpty = page.locator('.sleek-table, .empty-layout')
        await expect(tableOrEmpty.first()).toBeVisible()
    })

    test('5.5 — Hiển thị stats tài khoản', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // 3 stat cards: tổng, active, inactive
        const statCards = page.locator('.stat-card')
        const count = await statCards.count()
        expect(count).toBeGreaterThanOrEqual(3)
    })
})
