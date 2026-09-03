import request from './request'

export const login = (data) => request.post('/auth/login', data)
export const getMyProfile = () => request.get('/me')
export const updateMyProfile = (data) => request.patch('/me', data)
export const completeFirstLogin = (data) => request.post('/auth/first-login/complete', data)
