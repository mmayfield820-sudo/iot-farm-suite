import request from './request'

export const getAlarmList = (params) => request.get('/alarms', { params })
export const confirmAlarm = (id) => request.put(`/alarms/${id}/confirm`)
