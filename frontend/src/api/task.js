import request from './request'

export const listTasks = (params) => request.get('/tasks', { params })
export const getTask = (taskId) => request.get(`/tasks/${taskId}`)
export const updateTask = (taskId, data) => request.patch(`/tasks/${taskId}`, data)
export const createTaskChangeOrder = (taskId, data) => request.post(`/tasks/${taskId}/change-orders`, data)
export const createTemporaryTask = (farmId, data) => request.post(`/farms/${farmId}/temporary-tasks`, data)
export const completeTask = (taskId, data) => request.post(`/tasks/${taskId}/completions`, data)
export const createAdHocTask = (plotId, data) => request.post(`/plots/${plotId}/ad-hoc-tasks`, data)
