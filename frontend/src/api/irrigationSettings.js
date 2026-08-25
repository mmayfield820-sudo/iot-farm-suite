import request from './request'

export const getIrrigationSettings = (plotId) => request.get(`/plots/${plotId}/irrigation-settings`)
export const updateIrrigationSettings = (plotId, data) => request.put(`/plots/${plotId}/irrigation-settings`, data)
