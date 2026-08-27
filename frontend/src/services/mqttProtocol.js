export const MQTT_TOPICS = {
  telemetry: (deviceId) => `sensor/${deviceId}/data`,
  status: () => 'sensor/state',
  command: () => 'sensor/cmd',
  commandResult: () => 'sensor/ack',
}

export function buildControlCommand(deviceId, action, commandId = Date.now()) {
  const switchValue = action === 'open' ? 'on' : 'off'
  const numericCommandId = Number(commandId)
  const sequence = Number.isInteger(numericCommandId) ? numericCommandId : Date.now()
  return {
    commandId: String(sequence),
    topic: MQTT_TOPICS.command(),
    payload: { seq: sequence, ts: Date.now(), deviceId, switch: switchValue },
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
