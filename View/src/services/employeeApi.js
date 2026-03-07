import axios from 'axios'

const api = axios.create({
    baseURL: 'https://localhost:5107/api/Employees'
})

// Tự động gắn JWT token
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
 * Lấy danh sách nhân viên (có filter)
 * @param {{search?, departmentId?, positionId?, status?}} params
 */
export const getAll = (params = {}) => api.get('/', { params })

/** Lấy chi tiết nhân viên */
export const getById = (id) => api.get(`/${id}`)

/** Tạo nhân viên mới */
export const create = (data) => api.post('/', data)

/** Cập nhật nhân viên */
export const update = (id, data) => api.put(`/${id}`, data)

/** Xóa nhân viên */
export const deleteEmployee = (id) => api.delete(`/${id}`)

/**
 * Upload ảnh khuôn mặt
 * @param {number} id
 * @param {File} file
 */
export const uploadFace = (id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/${id}/face`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    })
}
