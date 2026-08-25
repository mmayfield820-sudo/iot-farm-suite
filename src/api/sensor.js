import request from './request'

export const getLatestSensorData = (plotId) => request.get('/sensors/latest', { params: { plotId } })
export const getSensorHistory = (params) => request.get('/sensors/history', { params })
