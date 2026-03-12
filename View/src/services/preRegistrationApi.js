import axios from 'axios'

// ── Axios instance cho các endpoint PUBLIC (không cần auth) ──
const publicApi = axios.create({
    baseURL: 'https://localhost:7107/api'
})

// ── Axios instance cho các endpoint ADMIN (cần auth) ──
const authApi = axios.create({
    baseURL: 'https://localhost:7107/api'
})

authApi.interceptors.request.use((config) => {
    const token = localStorage.getItem('v_shield_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

authApi.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('v_shield_token')
            localStorage.removeItem('v_shield_user')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

// ════════════════════════════════════════════════════════
// PUBLIC — Khách sử dụng (không cần đăng nhập)
// ════════════════════════════════════════════════════════

/** Validate token đăng ký → trả về tên nhân viên chủ trì & thời hạn */
export const validateToken = (token) => {
    return publicApi.get(`/pre-registrations/validate/${token}`)
}

/** Khách submit form đăng ký */
export const submitRegistration = (token, data) => {
    return publicApi.post(`/pre-registrations/submit/${token}`, data)
}

// ════════════════════════════════════════════════════════
// ADMIN — Yêu cầu đăng nhập
// ════════════════════════════════════════════════════════

/** Lấy danh sách đơn đăng ký (có phân trang & filter) */
export const getAll = (params = {}) => {
    return authApi.get('/pre-registrations', { params })
}

/** Lấy chi tiết đơn đăng ký */
export const getDetail = (id) => {
    return authApi.get(`/pre-registrations/${id}`)
}

/** Cập nhật trạng thái đơn (Approved / Rejected / Pending) */
export const updateStatus = (id, status) => {
    return authApi.patch(`/pre-registrations/${id}/status`, { status })
}

/** Tạo link đăng ký mới */
export const createLink = (data) => {
    return authApi.post('/registration-links', data)
}
