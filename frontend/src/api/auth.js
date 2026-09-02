import request from './request'

export const login = (data) => request.post('/auth/login', data)
export const getMyProfile = () => request.get('/me')
export const updateMyProfile = (data) => request.patch('/me', data)
export const completeFirstLogin = (data) => request.post('/auth/first-login/complete', data)
export const register = (data) => request.post('/auth/register', data)
export const getRegistrationResources = () => request.get('/registration-resources')
export const getRegistrationApplications = (params) => request.get('/registration-applications', { params })
export const approveRegistration = (id) => request.put(`/registration-applications/${id}/approve`)
export const rejectRegistration = (id, data) => request.put(`/registration-applications/${id}/reject`, data)
