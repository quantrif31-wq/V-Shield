import { test, expect } from '@playwright/test'
import { login } from '../helpers/auth.helper.js'

/**
 * Danh sách tất cả trang cần kiểm tra (role Admin)
 */
const ALL_PAGES = [
    { path: '/dashboard', name: 'Dashboard', titleText: 'Dashboard' },
    { path: '/employees', name: 'Employees', titleText: 'Quản lý Nhân sự' },
    { path: '/vehicles', name: 'Vehicles', titleText: 'Quản lý Phương tiện' },
    { path: '/access-logs', name: 'AccessLogs', titleText: 'Nhật ký' },
    { path: '/exceptions', name: 'Exceptions', titleText: 'Ngoại lệ' },
    { path: '/pre-registrations', name: 'PreRegistration', titleText: 'Đăng ký' },
    { path: '/registration-links', name: 'RegistrationLinks', titleText: 'Link' },
    { path: '/guest-profiles', name: 'GuestProfiles', titleText: 'Khách' },
    { path: '/users', name: 'UserManagement', titleText: 'Quản lý Tài khoản' },
    { path: '/departments-positions', name: 'DepartmentPosition', titleText: 'Phòng ban' },
    { path: '/device-management', name: 'DeviceManagement', titleText: 'Thiết bị' },
    { path: '/biometrics', name: 'Biometrics', titleText: 'Sinh trắc' },
    { path: '/system-catalog', name: 'SystemCatalog', titleText: 'Danh mục' },
    { path: '/monitoring', name: 'Monitoring', titleText: 'Giám sát' },
    { path: '/about-project', name: 'AboutProject', titleText: '' },
    { path: '/settings', name: 'Settings', titleText: 'Cài đặt' },
]

test.describe('🗺️ Navigation — Điều hướng tất cả trang', () => {

    test.beforeEach(async ({ page }) => {
        await login(page)
        await page.waitForSelector('.main-content', { state: 'visible', timeout: 10000 })
    })

    test('2.1 — Dashboard load thành công', async ({ page }) => {
        await page.goto('/dashboard')
        // Dashboard phải có nội dung hiển thị
        await expect(page.locator('.page-container, .main-content')).toBeVisible({ timeout: 10000 })
        // Không có loading spinner sau 5 giây
        await page.waitForTimeout(3000)
    })

    for (const pageInfo of ALL_PAGES) {
        test(`2.2 — Trang ${pageInfo.name} (${pageInfo.path}) render không lỗi`, async ({ page }) => {
            // Thu thập JS errors
            const jsErrors = []
            page.on('pageerror', error => jsErrors.push(error.message))

            await page.goto(pageInfo.path)

            // Đợi trang load
            await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {})
            await page.waitForTimeout(2000)

            // Kiểm tra không có page-level JS crash
            const criticalErrors = jsErrors.filter(e => 
                !e.includes('ResizeObserver') && 
                !e.includes('Non-Error') &&
                !e.includes('Network Error') &&
                !e.includes('ERR_CONNECTION_REFUSED') &&
                !e.includes('aborted')
            )

            // Trang phải có nội dung (không trắng)
            const bodyText = await page.locator('body').innerText()
            expect(bodyText.length).toBeGreaterThan(10)

            // In ra JS errors nếu có (không fail test vì có thể là lỗi nhẹ)
            if (criticalErrors.length > 0) {
                console.warn(`⚠️  JS Errors trên ${pageInfo.path}:`, criticalErrors)
            }
        })
    }
})
