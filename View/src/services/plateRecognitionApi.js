import http from './http'

export const getDetectedPlates = () => http.get('/BienSo/plates')
export const getCameraPlateSnapshot = () => http.get('/BienSo/camera-plates')
