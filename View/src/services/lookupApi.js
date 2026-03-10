import axios from 'axios'

const deptApi = axios.create({
    baseURL: 'https://localhost:7107/api/Departments'
})

const posApi = axios.create({
    baseURL: 'https://localhost:7107/api/Positions'
})

    // JWT interceptor cho cả hai
    ;[deptApi, posApi].forEach(api => {
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
    })

// ─── Departments ────────────────────────────────────────────
export const getDepartments = () => deptApi.get('/')
export const getDepartmentById = (id) => deptApi.get(`/${id}`)
export const createDepartment = (data) => deptApi.post('/', data)
export const updateDepartment = (id, data) => deptApi.put(`/${id}`, data)
export const deleteDepartment = (id) => deptApi.delete(`/${id}`)

// ─── Positions ──────────────────────────────────────────────
export const getPositions = () => posApi.get('/')
export const getPositionById = (id) => posApi.get(`/${id}`)
export const createPosition = (data) => posApi.post('/', data)
export const updatePosition = (id, data) => posApi.put(`/${id}`, data)
export const deletePosition = (id) => posApi.delete(`/${id}`)
