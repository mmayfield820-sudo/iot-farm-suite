import request from './request'

export const getIrrigationSettings = (plotId) => request.get(`/plots/${plotId}/irrigation-settings`)
export const getIrrigationRecommendation = (plotId) => request.get(`/plots/${plotId}/irrigation-recommendation`)
export const updateIrrigationSettings = (plotId, data) => request.put(`/plots/${plotId}/irrigation-settings`, data)
