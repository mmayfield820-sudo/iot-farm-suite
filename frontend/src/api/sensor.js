import request from './request'

export const getPlotMetrics = (plotId, params) => request.get(`/plots/${plotId}/metrics`, { params })
