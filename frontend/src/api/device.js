import request from './request'

export const getDeviceStatus = (plotId) => request.get(`/devices/plot/${plotId}/status`)

export const controlIrrigation = (data) => request.post('/irrigation/control', data)

export const getIrrigationRecords = (plotId) => request.get(`/irrigation/records?plotId=${plotId}`)

