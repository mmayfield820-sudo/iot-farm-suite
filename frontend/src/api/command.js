import request from './request'

export const createDeviceCommand = (deviceId, action, durationMinutes = null, activationType = 'manual') => request.post(`/devices/${deviceId}/commands`, {
  action,
  activationType,
  ...(durationMinutes == null ? {} : { durationMinutes }),
})
export const getCommandStatus = (commandId) => request.get(`/commands/${commandId}`)
