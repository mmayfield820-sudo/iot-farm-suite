import request from './request'

export const getThresholdConfig = (plotId) => request.get(`/plots/${plotId}/threshold`)
export const updateThresholdConfig = (plotId, data) => request.put(`/plots/${plotId}/threshold`, data)
