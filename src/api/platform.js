import request from './request'

export const getFarmList = (params) => request.get('/farms', { params })
export const getAllDevices = (params) => request.get('/devices', { params })
export const createDevice = (data) => request.post('/devices', data)
export const bindDevice = (deviceId, data) => request.put(`/devices/${deviceId}/binding`, data)
export const updateDeviceActive = (deviceId, active) => request.put(`/devices/${deviceId}/active`, { active })
export const getUserList = (params) => request.get('/users', { params })
export const saveUser = (id, data) => id ? request.put(`/users/${id}`, data) : request.post('/users', data)
export const updateUserActive = (id, active) => request.put(`/users/${id}/active`, { active })
export const resetUserPassword = (id) => request.post(`/users/${id}/reset-password`)
