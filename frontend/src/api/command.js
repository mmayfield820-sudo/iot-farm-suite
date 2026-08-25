import request from './request'

export const createDeviceCommand = (deviceId, action) => request.post(`/devices/${deviceId}/commands`, { action })
export const getCommandStatus = (commandId) => request.get(`/commands/${commandId}`)
