import { reactive } from 'vue'
import { login as loginApi, getMe } from '../services/authApi'

const state = reactive({
    token: localStorage.getItem('v_shield_token') || null,
    user: JSON.parse(localStorage.getItem('v_shield_user') || 'null'),
})

/**
 * Đăng nhập
 * @param {string} username
 * @param {string} password
 * @returns {Promise<boolean>}
 */
export async function login(username, password) {
    const res = await loginApi(username, password)
    const data = res.data

    state.token = data.token
    state.user = {
        username: data.username,
        fullName: data.fullName,
        role: data.role,
    }

    localStorage.setItem('v_shield_token', data.token)
    localStorage.setItem('v_shield_user', JSON.stringify(state.user))

    return true
}

/** Đăng xuất */
export function logout() {
    state.token = null
    state.user = null
    localStorage.removeItem('v_shield_token')
    localStorage.removeItem('v_shield_user')
}

/** Kiểm tra đã đăng nhập chưa */
export function isLoggedIn() {
    return !!state.token
}

/** Kiểm tra role */
export function hasRole(role) {
    return state.user?.role === role
}

/** Lấy thông tin user từ API (verify token) */
export async function fetchUser() {
    try {
        const res = await getMe()
        state.user = {
            username: res.data.username,
            fullName: res.data.fullName,
            role: res.data.role,
        }
        localStorage.setItem('v_shield_user', JSON.stringify(state.user))
        return true
    } catch {
        logout()
        return false
    }
}

export { state as authState }
