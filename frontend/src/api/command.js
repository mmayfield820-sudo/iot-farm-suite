import request from './request'

export const createDeviceCommand = (deviceId, action, plannedDuration) => request.post(`/devices/${deviceId}/commands`, {
  action,
  ...(plannedDuration ? { plannedDuration } : {}),
})
export const getCommandStatus = (commandId) => request.get(`/commands/${commandId}`)
