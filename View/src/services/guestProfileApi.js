import http from './http'

export const getGuestProfiles = (params = {}) => http.get('/guest-profiles', { params })
export const getGuestProfileDetail = (id) => http.get(`/guest-profiles/${id}`)
export const createGuestProfile = (data) => http.post('/guest-profiles', data)
export const updateGuestProfile = (id, data) => http.put(`/guest-profiles/${id}`, data)
export const deleteGuestProfile = (id) => http.delete(`/guest-profiles/${id}`)
