import axios from 'axios'
import { API_BASE_URL } from '../config/api'

const api = axios.create({
    baseURL: `${API_BASE_URL}/Vehicles`
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

/** Lấy danh sách tất cả phương tiện */
export const getAll = () => api.get('/')

/** Lấy danh mục loại xe */
export const getTypes = () => api.get('/types')

/** Lấy phương tiện theo ID */
export const getById = (id) => api.get(`/${id}`)

/** Tra cứu phương tiện theo biển số */
export const getByLicensePlate = (plate) => api.get(`/license-plate/${plate}`)

/** Lấy danh sách phương tiện của một nhân viên */
export const getByEmployeeId = (employeeId) => api.get(`/employee/${employeeId}`)

/** Đăng ký phương tiện mới */
export const create = (data) => api.post('/', data)

/** Cập nhật thông tin phương tiện */
export const update = (id, data) => api.put(`/${id}`, data)

/** Xóa đăng ký phương tiện */
export const deleteVehicle = (id) => api.delete(`/${id}`)
