import request from './request'

export const askAssistant = (data) => request.post('/consultations', data)
export const getConsultationHistory = (params) => request.get('/consultations', { params })
