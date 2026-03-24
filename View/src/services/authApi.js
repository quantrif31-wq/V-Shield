import axios from 'axios'
import { API_BASE_URL } from '../config/api'

const api = axios.create({
    baseURL: `${API_BASE_URL}/Auth`
})

// Tự động gắn JWT token vào mỗi request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('v_shield_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Tự động xử lý 401 → redirect login
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const requestUrl = String(error.config?.url || '').toLowerCase()
        const isLoginRequest = requestUrl.endsWith('/login') || requestUrl === '/login'

        if (error.response && error.response.status === 401 && !isLoginRequest) {
            localStorage.removeItem('v_shield_token')
            localStorage.removeItem('v_shield_user')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

/**
 * Đăng nhập
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{token, username, fullName, role, expiresAt}>}
 */
export const login = (username, password) => {
    return api.post('/login', { username, password })
}

/**
 * Lấy thông tin user đang đăng nhập
 * @returns {Promise<{userId, username, fullName, role, isActive, createdAt}>}
 */
export const getMe = () => {
    return api.get('/me')
}
