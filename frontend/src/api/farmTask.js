import request from './request'

export const previewManagementPlan = (plotId) => request.post(`/plots/${plotId}/plans/preview`, {})
export const generateManagementPlan = (plotId, regenerate = false, tasks = null) => request.post(`/plots/${plotId}/plans/generate`, { regenerate, tasks })
export const getPlotTasks = (plotId) => request.get(`/plots/${plotId}/tasks`)
export const getTodayTasks = () => request.get('/tasks/today')
export const getUpcomingTasks = (days = 7) => request.get('/tasks/upcoming', { params: { days } })
export const getCalendarTasks = (month, plotId) => request.get('/tasks/calendar', { params: { month, plotId } })
export const updateFarmTask = (taskId, data) => request.patch(`/tasks/${taskId}`, data)
export const completeFarmTask = (taskId, data) => request.post(`/tasks/${taskId}/complete`, data)
export const createTemporaryTask = (data) => request.post('/farm-tasks/temporary', data)
