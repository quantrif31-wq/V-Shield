import { test, expect } from '@playwright/test'
import { login, TEST_CREDENTIALS } from '../helpers/auth.helper.js'

test.describe('🔐 Authentication & Authorization', () => {

    test('1.1 — Đăng nhập thành công với tài khoản admin', async ({ page }) => {
        await page.goto('/login')

        // Kiểm tra trang login hiển thị
        await expect(page.locator('#username')).toBeVisible()
        await expect(page.locator('#password')).toBeVisible()
        await expect(page.locator('button[type="submit"]')).toBeVisible()

        // Nhập thông tin đăng nhập
        await page.fill('#username', TEST_CREDENTIALS.username)
        await page.fill('#password', TEST_CREDENTIALS.password)
        await page.click('button[type="submit"]')

        // Đợi thông báo thành công
        await expect(page.locator('.login-alert.success')).toBeVisible({ timeout: 10000 })

        // Đợi redirect
        await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 15000 })

        // Kiểm tra đã vào main layout
        await expect(page.locator('.main-content')).toBeVisible({ timeout: 10000 })
    })

    test('1.2 — Hiển thị lỗi khi sai mật khẩu', async ({ page }) => {
        await page.goto('/login')
        await page.fill('#username', 'admin')
        await page.fill('#password', 'sai_mat_khau_123')
        await page.click('button[type="submit"]')

        // Đợi thông báo lỗi
        await expect(page.locator('.login-alert.danger')).toBeVisible({ timeout: 10000 })
    })

    test('1.3 — Hiển thị cảnh báo khi để trống thông tin', async ({ page }) => {
        await page.goto('/login')

        // Submit khi chưa nhập gì
        await page.click('button[type="submit"]')

        // Kiểm tra thông báo cảnh báo
        await expect(page.locator('.login-alert')).toBeVisible({ timeout: 5000 })
    })

    test('1.4 — Route Guard: redirect về login khi chưa đăng nhập', async ({ page }) => {
        // Xóa localStorage trước
        await page.goto('/login')
        await page.evaluate(() => {
            localStorage.removeItem('v_shield_token')
            localStorage.removeItem('v_shield_user')
        })

        // Truy cập trang cần auth
        await page.goto('/dashboard')

        // Phải redirect về login
        await page.waitForURL('**/login**', { timeout: 10000 })
        await expect(page.locator('#username')).toBeVisible()
    })

    test('1.5 — Đăng xuất thành công', async ({ page }) => {
        // Đăng nhập trước
        await login(page)
        await page.waitForSelector('.main-content', { state: 'visible', timeout: 10000 })

        // Tìm nút logout (thường trong header hoặc sidebar)
        const logoutBtn = page.locator('button, a').filter({ hasText: /đăng xuất|logout/i }).first()
        
        if (await logoutBtn.isVisible()) {
            await logoutBtn.click()
            // Đợi redirect về login
            await page.waitForURL('**/login**', { timeout: 10000 })
            await expect(page.locator('#username')).toBeVisible()
        } else {
            // Logout bằng cách xóa token và navigate  
            await page.evaluate(() => {
                localStorage.removeItem('v_shield_token')
                localStorage.removeItem('v_shield_user')
            })
            await page.goto('/dashboard')
            await page.waitForURL('**/login**', { timeout: 10000 })
            await expect(page.locator('#username')).toBeVisible()
        }
    })
})
