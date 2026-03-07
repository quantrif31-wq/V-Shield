import axios from 'axios'

const api = axios.create({
    baseURL: 'https://localhost:5107/api/Statistics'
})

// Tự động gắn JWT token vào mỗi request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('v_shield_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

api.interceptors.response.use(
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

/**
 * Lấy thống kê tổng quan nhân viên
 * @returns {Promise<{totalEmployees, activeEmployees, inactiveEmployees, byDepartment, byPosition, calculatedAt}>}
 */
export const getSummary = () => api.get('/employees/summary').then(res => res.data)
