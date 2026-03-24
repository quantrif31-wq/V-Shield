import http from './http'

export const getDeviceOverview = () => http.get('/device-management/overview')
export const getCameras = (params = {}) => http.get('/device-management/cameras', { params })
export const createCamera = (data) => http.post('/device-management/cameras', data)
export const updateCamera = (id, data) => http.put(`/device-management/cameras/${id}`, data)
export const deleteCamera = (id) => http.delete(`/device-management/cameras/${id}`)

export const getGates = (params = {}) => http.get('/device-management/gates', { params })
export const createGate = (data) => http.post('/device-management/gates', data)
export const updateGate = (id, data) => http.put(`/device-management/gates/${id}`, data)
export const deleteGate = (id) => http.delete(`/device-management/gates/${id}`)
