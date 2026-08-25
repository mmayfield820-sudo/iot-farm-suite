import request from './request'

export const getAlertRules = () => request.get('/alert-rules')
export const saveAlertRule = (data) => request.post('/alert-rules', data)
