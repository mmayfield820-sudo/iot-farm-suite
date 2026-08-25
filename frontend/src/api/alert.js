import request from './request'

export const getAlertList = (params) => request.get('/alerts', { params })

export const acknowledgeAlert = (alertId) => request.post(`/alerts/${alertId}/ack`)
