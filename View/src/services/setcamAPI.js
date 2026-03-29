import axios from 'axios'
import { API_BASE_URL } from '../config/api'

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 15000,
})

// ================= CAMERA =================

// lấy danh sách
export async function getCameras() {
    const res = await api.get('/SetCam')
    return res.data
}

// lấy theo id
export async function getCameraById(id) {
    const res = await api.get(`/SetCam/${id}`)
    return res.data
}

// thêm
export async function createCamera(data) {
    const res = await api.post('/SetCam', data)
    return res.data
}

// cập nhật
export async function updateCamera(id, data) {
    const res = await api.put(`/SetCam/${id}`, data)
    return res.data
}

// xóa
export async function deleteCamera(id) {
    const res = await api.delete(`/SetCam/${id}`)
    return res.data
}

// ================= 🔥 GO2RTC =================

// reload + tự update UrlView
export async function reloadGo2rtc() {
    const res = await api.post('/SetCam/reload-go2rtc')
    return res.data
}

// stop
export async function stopGo2rtc() {
    const res = await api.post('/SetCam/stop-go2rtc')
    return res.data
}