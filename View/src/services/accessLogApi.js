import http from './http'

export const getAccessLogs = (params = {}) => http.get('/access-logs', { params })
export const getAccessLogSummary = () => http.get('/access-logs/summary')
export const getAccessLogDetail = (id) => http.get(`/access-logs/${id}`)
export const getExceptions = (params = {}) => http.get('/access-logs/exceptions', { params })
