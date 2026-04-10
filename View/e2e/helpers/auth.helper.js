/**
 * Helper đăng nhập cho các test case
 * Sử dụng tài khoản admin mặc định từ appsettings.json > SeedAdmin
 */
export const TEST_CREDENTIALS = {
    username: 'admin',
    password: 'Admin@123',
}

/**
 * Đăng nhập vào hệ thống V-Shield
 * @param {import('@playwright/test').Page} page
 * @param {object} [credentials]
 * @param {string} [credentials.username]
 * @param {string} [credentials.password]
 */
export async function login(page, credentials = TEST_CREDENTIALS) {
    await page.goto('/login')
    await page.waitForSelector('#username', { state: 'visible' })
    await page.fill('#username', credentials.username)
    await page.fill('#password', credentials.password)
    await page.click('button[type="submit"]')  
    // Đợi redirect về dashboard hoặc trang chính
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 15000 })
}

/**
 * Đăng nhập và đợi trang Dashboard load xong
 * @param {import('@playwright/test').Page} page
 */
export async function loginAndWaitForDashboard(page) {
    await login(page)
    // Đợi cho main content render
    await page.waitForSelector('.main-content', { state: 'visible', timeout: 10000 })
}

/**
 * Kiểm tra console errors trên trang hiện tại
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<string[]>}
 */
export async function collectConsoleErrors(page) {
    const errors = []
    page.on('console', msg => {
        if (msg.type() === 'error') {
            errors.push(msg.text())
        }
    })
    return errors
}
