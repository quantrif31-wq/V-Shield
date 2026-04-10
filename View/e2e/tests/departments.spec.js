import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('🏢 Departments & Positions — Phòng ban & Chức vụ', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/departments-positions')
        await page.waitForSelector('.page-container', { state: 'visible', timeout: 10000 })
    })

    test('6.1 — Trang phòng ban & chức vụ load thành công', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        await expect(page.locator('h1.page-title')).toContainText('Phòng ban')

        // Kiểm tra 2 bảng (phòng ban + chức vụ)
        const tables = page.locator('.sleek-table')
        const count = await tables.count()
        expect(count).toBeGreaterThanOrEqual(2)
    })

    test('6.2 — Mở form thêm phòng ban', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Click nút "Thêm" trong card Phòng ban (nút đầu tiên)
        const addDeptBtn = page.locator('.card-header-mini').first().locator('button').filter({ hasText: 'Thêm' })
        await addDeptBtn.click()

        await expect(page.locator('.modern-modal')).toBeVisible({ timeout: 5000 })
        await expect(page.locator('.modal-top h3')).toContainText('Thêm Phòng ban')
    })

    test('6.3 — Tạo phòng ban mới', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const addDeptBtn = page.locator('.card-header-mini').first().locator('button').filter({ hasText: 'Thêm' })
        await addDeptBtn.click()
        await expect(page.locator('.modern-modal')).toBeVisible({ timeout: 5000 })

        const deptName = `AutoTest PB ${Date.now().toString().slice(-4)}`
        await page.locator('.modern-modal input.sleek-input').fill(deptName)
        await page.locator('.modern-modal button[type="submit"]').click()

        await expect(page.locator('.modern-modal')).toBeHidden({ timeout: 10000 })
    })

    test('6.4 — Mở form thêm chức vụ', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Click nút "Thêm" trong card Chức vụ (nút thứ 2)
        const addPosBtn = page.locator('.card-header-mini').nth(1).locator('button').filter({ hasText: 'Thêm' })
        await addPosBtn.click()

        await expect(page.locator('.modern-modal')).toBeVisible({ timeout: 5000 })
        await expect(page.locator('.modal-top h3')).toContainText('Thêm Chức vụ')
    })

    test('6.5 — Tạo chức vụ mới', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        const addPosBtn = page.locator('.card-header-mini').nth(1).locator('button').filter({ hasText: 'Thêm' })
        await addPosBtn.click()
        await expect(page.locator('.modern-modal')).toBeVisible({ timeout: 5000 })

        const posName = `AutoTest CV ${Date.now().toString().slice(-4)}`
        await page.locator('.modern-modal input.sleek-input').fill(posName)
        await page.locator('.modern-modal button[type="submit"]').click()

        await expect(page.locator('.modern-modal')).toBeHidden({ timeout: 10000 })
    })
})
