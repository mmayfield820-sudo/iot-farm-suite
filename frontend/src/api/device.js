import request from './request'

export const getDeviceStatus = (deviceId) => request.get(`/devices/${deviceId}/status`)

export const getIrrigationRecords = (plotId) => request.get(`/irrigation/records?plotId=${plotId}`)
