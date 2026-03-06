import axios from "axios"

const api = axios.create({
    baseURL: "https://localhost:7103/api/FaceID"
})

export const startCamera = (ip) => {
    return api.post(`/start?ip=${encodeURIComponent(ip)}`)
}

export const stopCamera = () => {
    return api.post(`/stop`)
}

export const getStatus = () => {
    return api.get(`/status`)
}