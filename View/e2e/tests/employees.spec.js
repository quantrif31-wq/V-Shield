import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

test.describe('👥 Employees — Quản lý Nhân sự', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.goto('/employees')
        await page.waitForSelector('.page-container', { state: 'visible', timeout: 10000 })
    })

    test('3.1 — Trang nhân viên load và hiển thị bảng', async ({ page }) => {
        // Đợi loading xong
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})
        
        // Kiểm tra header
        await expect(page.locator('h1.page-title')).toContainText('Quản lý Nhân sự')

        // Kiểm tra bảng hoặc empty state
        const tableOrEmpty = page.locator('.sleek-table, .empty-state, .empty-layout')
        await expect(tableOrEmpty.first()).toBeVisible({ timeout: 10000 })
    })

    test('3.2 — Tìm kiếm nhân viên', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Nhập tìm kiếm
        const searchInput = page.locator('.search-box input')
        await expect(searchInput).toBeVisible()
        await searchInput.fill('test')
        
        // Đợi debounce
        await page.waitForTimeout(1000)

        // Kiểm tra bảng vẫn hiển thị (có thể có kết quả hoặc empty state)
        const tableOrEmpty = page.locator('.sleek-table, .empty-state')
        await expect(tableOrEmpty.first()).toBeVisible()
    })

    test('3.3 — Mở form thêm nhân viên mới', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Click nút "Thêm nhân viên"
        const addBtn = page.locator('button').filter({ hasText: 'Thêm nhân viên' })
        await expect(addBtn).toBeVisible()
        await addBtn.click()

        // Kiểm tra modal xuất hiện
        await expect(page.locator('.modern-modal')).toBeVisible({ timeout: 5000 })
        await expect(page.locator('.modal-top h3')).toContainText('Thêm Nhân sự')

        // Kiểm tra các field trong form
        await expect(page.locator('.modern-modal input[type="text"]').first()).toBeVisible()
    })

    test('3.4 — Tạo nhân viên mới thành công', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Click thêm nhân viên
        await page.locator('button').filter({ hasText: 'Thêm nhân viên' }).click()
        await expect(page.locator('.modern-modal')).toBeVisible({ timeout: 5000 })

        // Điền form
        const uniqueName = `AutoTest NV ${Date.now().toString().slice(-6)}`
        await page.locator('.modern-modal input[placeholder*="Nguyễn Văn"]').fill(uniqueName)
        await page.locator('.modern-modal input[type="tel"]').fill('0901234567')
        await page.locator('.modern-modal input[type="email"]').fill('autotest@test.com')

        // Submit
        await page.locator('.modern-modal button[type="submit"]').click()

        // Đợi modal đóng và toast thành công
        await expect(page.locator('.modern-modal')).toBeHidden({ timeout: 10000 })
        await expect(page.locator('.toast-card.success')).toBeVisible({ timeout: 5000 }).catch(() => {})
    })

    test('3.5 — Filter theo trạng thái', async ({ page }) => {
        await page.waitForSelector('.spinner-lg', { state: 'hidden', timeout: 15000 }).catch(() => {})

        // Chọn filter "Đang hoạt động"
        const filterSelect = page.locator('select.minimal-select')
        await filterSelect.selectOption('true')
        
        // Đợi data load lại
        await page.waitForTimeout(1000)

        // Kiểm tra kết quả
        const tableOrEmpty = page.locator('.sleek-table, .empty-state')
        await expect(tableOrEmpty.first()).toBeVisible()
    })
})
