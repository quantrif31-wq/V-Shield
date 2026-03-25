import axios from 'axios'
import { API_BASE_URL } from '../config/api'

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 15000,
})

export async function verifyDynamicQr(qrPayload, scannerDevice = 'WEB_SCANNER') {
    const response = await api.post('/QR_Dong/verify', {
        qrPayload,
        scannerDevice,
    })
    return response.data
}

export default api
