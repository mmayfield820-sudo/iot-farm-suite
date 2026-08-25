import request from './request'

export const login = (data) => request.post('/auth/login', data)
export const register = (data) => request.post('/auth/register', data)
export const getProfile = () => request.get('/auth/profile')
export const getRegistrationApplications = (params) => request.get('/registration-applications', { params })
export const approveRegistration = (id) => request.put(`/registration-applications/${id}/approve`)
export const rejectRegistration = (id, data) => request.put(`/registration-applications/${id}/reject`, data)
