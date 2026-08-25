export const MQTT_TOPICS = {
  telemetry: (deviceId) => `farm/telemetry/${deviceId}`,
  status: (deviceId) => `farm/status/${deviceId}`,
  command: (deviceId) => `farm/command/${deviceId}`,
  commandResult: (deviceId) => `farm/command_result/${deviceId}`,
}

export function buildControlCommand(deviceId, action, commandId = `CMD${Date.now()}`) {
  return {
    topic: MQTT_TOPICS.command(deviceId),
    payload: { commandId, deviceId, action: action === 'open' ? 'irrigation_on' : 'irrigation_off', ts: new Date().toISOString() },
  }
}

export function normalizeTelemetry(message) {
  const required = ['deviceNo', 'deviceId', 'type', 'value', 'msgId', 'ts']
  const missing = required.filter((key) => message[key] === undefined || message[key] === '')
  if (missing.length) return { valid: false, reason: `缺少字段：${missing.join('、')}` }
  if (!['temperature', 'humidity'].includes(message.type)) return { valid: false, reason: '不支持的遥测类型' }
  return { valid: true, data: { ...message, value: Number(message.value), receivedAt: new Date().toISOString() } }
}

export function commandResultLabel(result) {
  return { success: '成功', failed: '失败', timeout: '超时' }[result] || '未知'
}
