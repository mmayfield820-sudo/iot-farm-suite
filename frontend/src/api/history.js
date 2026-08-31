import request from './request'

export const getPlotManagementHistory = (plotId, params) => request.get(`/plots/${plotId}/management-history`, { params })
