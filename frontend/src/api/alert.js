import request from './request'

export const getAlertList = (params) => request.get('/alerts', { params })

export const confirmAlert = (alertId) => request.put(`/alerts/${alertId}/confirm`)

export const resolveAlert = (alertId) => request.put(`/alerts/${alertId}/resolve`)

