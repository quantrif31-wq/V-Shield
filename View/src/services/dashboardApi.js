import http from './http'

export const getDashboardOverview = () => http.get('/dashboard/overview')
