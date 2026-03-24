import http from './http'

export const getBiometricOverview = (params = {}) => http.get('/biometrics/overview', { params })
