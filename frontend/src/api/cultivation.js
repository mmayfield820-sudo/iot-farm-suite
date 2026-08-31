import request from './request'

export const getCultivationTemplates = () => request.get('/cultivation-templates')
export const createCultivationTemplate = (data) => request.post('/cultivation-templates', data)
export const updateCultivationTemplate = (templateId, data) => request.put(`/cultivation-templates/${templateId}`, data)
export const deleteCultivationTemplate = (templateId) => request.delete(`/cultivation-templates/${templateId}`)

export const getPlotPlanting = (plotId) => request.get(`/plots/${plotId}/planting`)
export const updatePlotPlanting = (plotId, data) => request.put(`/plots/${plotId}/planting`, data)
export const getPlotStage = (plotId) => request.get(`/plots/${plotId}/stage`)
export const updatePlotStage = (plotId, data) => request.put(`/plots/${plotId}/stage`, data)
export const getPlotTimeline = (plotId, params = {}) => request.get(`/plots/${plotId}/timeline`, { params })
