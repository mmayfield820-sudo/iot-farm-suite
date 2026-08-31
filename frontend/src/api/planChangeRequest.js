import request from './request'

export const getPlanChangeRequests = (params) => request.get('/plan-change-requests', { params })
export const approvePlanChangeRequest = (requestId, data = {}) => request.post(`/plan-change-requests/${requestId}/approve`, data)
export const rollbackPlanChangeRequest = (requestId, data) => request.post(`/plan-change-requests/${requestId}/rollback`, data)
