import request from './request'

export const getIrrigationAdvice = (plotId) => request.get(`/plots/${plotId}/irrigation-advice`)
