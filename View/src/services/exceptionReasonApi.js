import http from './http'

export const getExceptionReasons = () => http.get('/exception-reasons')
export const createExceptionReason = (data) => http.post('/exception-reasons', data)
export const updateExceptionReason = (id, data) => http.put(`/exception-reasons/${id}`, data)
export const deleteExceptionReason = (id) => http.delete(`/exception-reasons/${id}`)
