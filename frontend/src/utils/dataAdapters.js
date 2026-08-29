const firstDefined = (...values) => values.find((value) => value !== undefined && value !== null)

export const normalizeId = (value) => value === undefined || value === null || value === '' ? '' : String(value)

export function unwrapList(response) {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.records)) return response.records
  if (Array.isArray(response?.items)) return response.items
  if (Array.isArray(response?.content)) return response.content
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.data?.records)) return response.data.records
  for (const key of ['plots', 'farms', 'devices', 'alerts', 'users', 'reports', 'records']) {
    if (Array.isArray(response?.[key])) return response[key]
    if (Array.isArray(response?.data?.[key])) return response.data[key]
  }
  return []
}

export function parseDate(value) {
  if (!value) return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  const normalized = typeof value === 'string' && !value.includes('T') ? value.replace(' ', 'T') : value
  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDateTime(value, fallback = '-') {
  const date = parseDate(value)
  if (!date) return fallback
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
  }).formatToParts(date).reduce((result, part) => ({ ...result, [part.type]: part.value }), {})
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`
}

export function isHeartbeatOnline(lastHeartbeat, offlineMinutes = 30) {
  const heartbeat = parseDate(lastHeartbeat)
  if (!heartbeat) return false
  return Date.now() - heartbeat.getTime() <= offlineMinutes * 60 * 1000
}

export function normalizeFarm(row = {}) {
  return {
    ...row,
    farmId: normalizeId(firstDefined(row.farmId, row.farm_id, row.id)),
    name: firstDefined(row.name, row.farmName, row.farm_name, '未命名农场'),
    farmName: firstDefined(row.farmName, row.farm_name, row.name, '未命名农场'),
    city: firstDefined(row.city, ''),
    address: firstDefined(row.address, row.location, ''),
    active: Boolean(firstDefined(row.active, row.Active, true)),
    createdAt: formatDateTime(firstDefined(row.createdAt, row.created_at, ''), ''),
  }
}

export function normalizeDevice(row = {}, options = {}) {
  const typeMap = { temperature: '温度传感器', humidity: '湿度传感器', irrigation: '灌溉设备' }
  const lastHeartbeat = firstDefined(row.lastHeartbeat, row.last_heartbeat, row.lastSeenAt, row.last_seen_at, '')
  const statusOnline = row.status === undefined || row.status === null ? undefined : ['online', '在线'].includes(row.status)
  const online = firstDefined(row.online, row.deviceOnline, statusOnline, isHeartbeatOnline(lastHeartbeat, options.offlineMinutes))
  const rawType = firstDefined(row.type, row.deviceType, row.device_type, '未知设备')
  const type = typeMap[rawType] || rawType
  const rawWorkStatus = firstDefined(row.workStatus, row.work_status, row.running === true ? 'running' : undefined, 'stopped')
  const running = ['running', '运行中'].includes(rawWorkStatus)
  const plotId = normalizeId(firstDefined(row.plotId, row.plot_id, row.plotNo))
  return {
    ...row,
    id: normalizeId(firstDefined(row.id, row.deviceId, row.device_id)),
    deviceId: normalizeId(firstDefined(row.deviceId, row.device_id, row.id)),
    plotId,
    plotNo: plotId,
    deviceNo: firstDefined(row.deviceNo, row.deviceCode, row.device_code, ''),
    deviceUuid: firstDefined(row.deviceUuid, row.device_uuid, row.mqttDeviceId, row.mqtt_device_id, row.mqttId, ''),
    type,
    online: Boolean(online),
    status: online ? '在线' : '离线',
    workStatusCode: running ? 'running' : 'stopped',
    workStatus: running ? '运行中' : '已停止采集',
    running,
    lastHeartbeatRaw: lastHeartbeat,
    lastHeartbeat: formatDateTime(lastHeartbeat, ''),
    createdAt: formatDateTime(firstDefined(row.createdAt, row.created_at, ''), ''),
    latestValue: firstDefined(row.latestValue, row.latest_value, row.value, '-'),
  }
}

export function normalizeThreshold(row = {}) {
  return {
    configId: normalizeId(firstDefined(row.configId, row.config_id, row.id)),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id)),
    threshold: Number(firstDefined(row.threshold, row.soilMoistureThreshold, row.soil_moisture_threshold, 35)),
    irrigationDuration: Number(firstDefined(row.irrigationDuration, row.irrigationLengthMinutes, row.irrigation_length_minutes, row.maxDuration, 30)),
    irrigationInterval: Number(firstDefined(row.irrigationInterval, row.irrigationIntervalMinutes, row.irrigation_interval_minutes, row.cooldown, 60)),
    updatedBy: normalizeId(firstDefined(row.updatedBy, row.updated_by)),
    updatedAt: formatDateTime(firstDefined(row.updatedAt, row.updated_at, ''), ''),
  }
}

export function normalizeReport(row = {}) {
  const createdAt = firstDefined(row.createdAt, row.created_at, row.updateTime, '')
  return {
    reportId: normalizeId(firstDefined(row.reportId, row.report_id, row.id)),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id)),
    humidity: Number(firstDefined(row.humidity, row.plotMoisture, row.plot_moisture, 0)),
    temperature: Number(firstDefined(row.temperature, 0)),
    createdAtRaw: createdAt,
    createdAt: formatDateTime(createdAt, ''),
  }
}

export function normalizeIrrigationRecord(row = {}) {
  const startTime = firstDefined(row.startTime, row.start_time, row.startedAt, row.started_at, row.requestedAt, row.requested_at, '')
  const endTime = firstDefined(row.endTime, row.end_time, row.endedAt, row.ended_at, '')
  const start = parseDate(startTime)
  const end = parseDate(endTime)
  const statusMap = { pending: '待确认', in_progress: '进行中', success: '成功', failed: '失败', timeout: '超时', 执行中: '进行中' }
  const actionMap = { irrigation_on: '开启', irrigation_off: '关闭', on: '开启', off: '关闭' }
  const activationMap = { manual: '手动', auto: '自动' }
  const plannedDuration = firstDefined(row.plannedDuration, row.planned_duration, null)
  const rawActualDuration = firstDefined(
    row.actualDuration,
    row.actual_duration,
    row.duration === '-' ? null : row.duration,
    start && end ? Math.round(((end - start) / 60000) * 100) / 100 : null,
  )
  const actualDuration = rawActualDuration === undefined || rawActualDuration === null || rawActualDuration === '' ? null : rawActualDuration
  const durationText = actualDuration !== null
    ? `${plannedDuration ? `计划 ${plannedDuration} / ` : ''}实际 ${actualDuration} 分钟`
    : plannedDuration ? `计划 ${plannedDuration} / ${endTime ? '暂无实际值' : '进行中'}` : '-'
  return {
    ...row,
    recordId: normalizeId(firstDefined(row.recordId, row.record_id, row.id)),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id)),
    deviceId: normalizeId(firstDefined(row.deviceId, row.device_id)),
    operationType: actionMap[firstDefined(row.operationType, row.action, row.actionType, row.action_type, '')] || firstDefined(row.operationType, row.action, row.actionType, row.action_type, ''),
    activationType: activationMap[firstDefined(row.activationType, row.activation_type, row.source)] || firstDefined(row.activationType, row.activation_type, row.source, '手动'),
    operatorId: normalizeId(firstDefined(row.operatorId, row.operator_id)),
    operator: firstDefined(row.operator, row.operatorName, row.operator_name, row.operatorUsername, '系统'),
    startTimeRaw: startTime,
    endTimeRaw: endTime,
    startTime: formatDateTime(startTime, ''),
    endTime: formatDateTime(endTime, ''),
    plannedDuration,
    duration: actualDuration ?? '-',
    durationText,
    status: statusMap[row.status] || firstDefined(row.status, '失败'),
    source: activationMap[firstDefined(row.source, row.activationType, row.activation_type)] || firstDefined(row.source, row.activationType, row.activation_type, '手动'),
  }
}

export function normalizeCommandRecord(row = {}) {
  const action = firstDefined(row.action, row.actionType, row.action_type, '')
  const status = firstDefined(row.status, 'failed')
  const actionMap = { irrigation_on: '开启', irrigation_off: '关闭', on: '开启', off: '关闭' }
  const statusMap = { pending: '等待设备响应', success: '成功', failed: '失败', timeout: '超时' }
  return {
    ...row,
    commandId: String(firstDefined(row.commandId, row.command_id, '')),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id)),
    deviceId: normalizeId(firstDefined(row.deviceId, row.device_id)),
    action,
    actionText: actionMap[action] || action,
    status: statusMap[status] || status,
    plannedDuration: firstDefined(row.plannedDuration, row.planned_duration, null),
    sentAt: formatDateTime(firstDefined(row.sentAt, row.requestedAt, row.requested_at, ''), ''),
    resultAt: formatDateTime(firstDefined(row.resultAt, row.executedAt, row.executed_at, ''), ''),
  }
}

export function normalizeAlert(row = {}) {
  const statusMap = { active: '未处理', acknowledged: '处理中', recovered: '已处理', 已确认: '处理中', 已恢复: '已处理' }
  const rawType = firstDefined(row.type, row.metricType, row.metric_type, row.alertType, row.alert_type, '未知告警')
  const typeMap = {
    humidity: '湿度过低',
    temperature: '温度异常',
    low_moisture: '湿度过低',
    device_offline: '设备离线',
    device_fault: '设备故障',
    irrigation_failed: '灌溉失败',
  }
  const occurTime = firstDefined(row.occurTime, row.triggeredAt, row.triggered_at, row.alertDatetime, row.alert_datetime, '')
  const handledAt = firstDefined(row.handledAt, row.handled_at, '')
  return {
    ...row,
    alertId: normalizeId(firstDefined(row.alertId, row.alert_id, row.id)),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id, row.plotNo)),
    deviceId: normalizeId(firstDefined(row.deviceId, row.device_id)),
    typeCode: rawType,
    type: typeMap[rawType] || rawType,
    reason: firstDefined(row.reason, row.alertDescription, row.alert_description, '暂无告警说明'),
    value: firstDefined(row.value, row.triggerValue, row.alertValue, row.alert_value, '-'),
    threshold: firstDefined(row.threshold, row.alertThreshold, row.alert_threshold, '-'),
    occurTime: formatDateTime(occurTime, ''),
    status: statusMap[row.status] || statusMap[row.alert_status] || firstDefined(row.status, row.alert_status, '未处理'),
    handledBy: normalizeId(firstDefined(row.handledBy, row.handled_by)),
    handledAt: formatDateTime(handledAt, ''),
  }
}

export function normalizePlot(row = {}, related = {}) {
  const report = normalizeReport(related.report || row.latestReport || row.latest_report || row)
  const threshold = normalizeThreshold(related.threshold || row.thresholdConfig || row.threshold_config || row)
  const deviceRows = related.devices || row.devices || []
  const devices = Array.isArray(deviceRows) ? deviceRows.map((item) => normalizeDevice(item, related)) : Object.values(deviceRows).map((item) => normalizeDevice(item, related))
  const irrigationRecords = (related.irrigationRecords || row.irrigationRecords || []).map(normalizeIrrigationRecord).sort((a, b) => (parseDate(b.startTimeRaw || b.startTime)?.getTime() || 0) - (parseDate(a.startTimeRaw || a.startTime)?.getTime() || 0))
  const alerts = (related.alerts || row.alerts || []).map(normalizeAlert)
  const deviceByType = {
    temperature: devices.find((item) => item.type.includes('温度')),
    humidity: devices.find((item) => item.type.includes('湿度')),
    irrigation: devices.find((item) => item.type.includes('灌溉')),
  }
  const irrigationDevice = deviceByType.irrigation
  const activeIrrigation = irrigationDevice
    ? irrigationDevice.workStatusCode === 'running'
    : Boolean(row.irrigating)
  const lastIrrigation = irrigationRecords.find((item) => item.operationType === '开启')
  const allOnline = devices.length > 0 && devices.every((item) => item.online)
  const plotId = normalizeId(firstDefined(row.plotId, row.plot_id, row.id))
  const humidity = Number(firstDefined(row.humidity, report.humidity, 0))
  const status = !allOnline ? 'offline' : activeIrrigation ? 'irrigating' : humidity < threshold.threshold ? 'alert' : 'normal'
  const heartbeatTimes = devices.map((item) => parseDate(item.lastHeartbeatRaw || item.lastHeartbeat)).filter(Boolean).sort((a, b) => b - a)
  return {
    ...row,
    plotId,
    farmId: normalizeId(firstDefined(row.farmId, row.farm_id)),
    farmName: firstDefined(row.farmName, row.farm_name, related.farm?.farmName, related.farm?.name, '未命名农场'),
    plotName: firstDefined(row.plotName, row.plot_name, row.name, `地块 ${plotId}`),
    location: firstDefined(row.location, ''),
    cropName: firstDefined(row.cropName, row.crop_name, row.crop, '暂未种植'),
    cropStage: firstDefined(row.cropStage, row.crop_stage, row.description, '未填写生长阶段'),
    description: firstDefined(row.description, ''),
    active: Boolean(firstDefined(row.active, row.Active, true)),
    temperature: Number(firstDefined(row.temperature, report.temperature, 0)),
    humidity,
    updateTime: firstDefined(row.updateTime, report.createdAt, ''),
    threshold: threshold.threshold,
    irrigationDuration: threshold.irrigationDuration,
    irrigationInterval: threshold.irrigationInterval,
    maxDuration: threshold.irrigationDuration,
    deviceOnline: allOnline,
    onlineDeviceCount: devices.filter((item) => item.online).length,
    runningDeviceCount: devices.filter((item) => item.running).length,
    deviceCount: devices.length,
    dataState: row.dataState || (report.createdAtRaw && isHeartbeatOnline(report.createdAtRaw, related.staleDataMinutes || 15) ? 'realtime' : 'delayed'),
    irrigating: Boolean(activeIrrigation),
    status: row.status || status,
    lastHeartbeat: heartbeatTimes[0] ? formatDateTime(heartbeatTimes[0]) : '',
    sensorId: firstDefined(row.sensorId, deviceByType.humidity?.deviceNo, deviceByType.temperature?.deviceNo, '-'),
    valveId: firstDefined(row.valveId, deviceByType.irrigation?.deviceNo, '-'),
    deviceId: firstDefined(row.deviceId, deviceByType.irrigation?.deviceId, deviceByType.irrigation?.deviceNo, '-'),
    devices: deviceByType,
    deviceList: devices,
    lastIrrigation: firstDefined(row.lastIrrigation, lastIrrigation?.startTime, ''),
    lastIrrigationDuration: firstDefined(row.lastIrrigationDuration, lastIrrigation?.duration, null),
    unhandledAlerts: alerts.filter((item) => item.status === '未处理').length,
  }
}

export function reportsToTrend(rows = [], threshold) {
  const reports = rows.map(normalizeReport).sort((a, b) => (parseDate(a.createdAtRaw || a.createdAt)?.getTime() || 0) - (parseDate(b.createdAtRaw || b.createdAt)?.getTime() || 0))
  return {
    times: reports.map((item) => formatDateTime(item.createdAt).slice(5, 16)),
    temperature: reports.map((item) => item.temperature),
    soilHumidity: reports.map((item) => item.humidity),
    events: [],
    threshold,
  }
}

export function overviewMetricsToReport(metrics = [], plotId = '') {
  const temperature = metrics.find((item) => item.type === 'temperature')
  const humidity = metrics.find((item) => item.type === 'humidity')
  const timestamps = metrics.map((item) => parseDate(item.ts)).filter(Boolean).sort((a, b) => b - a)
  return {
    plotId,
    temperature: Number(temperature?.value ?? 0),
    humidity: Number(humidity?.value ?? 0),
    createdAt: timestamps[0]?.toISOString() || '',
  }
}

export function metricSeriesToTrend(temperatureRows = [], humidityRows = [], threshold = 35, irrigationRows = []) {
  const temperatureByTime = new Map(temperatureRows.map((item) => [item.ts, Number(item.value)]))
  const humidityByTime = new Map(humidityRows.map((item) => [item.ts, Number(item.value)]))
  const timestamps = [...new Set([...temperatureByTime.keys(), ...humidityByTime.keys()])]
    .filter((value) => parseDate(value))
    .sort((a, b) => parseDate(a) - parseDate(b))
  const timestampValues = timestamps.map((value) => parseDate(value).getTime())
  const eventsByIndex = new Map()
  irrigationRows.map(normalizeIrrigationRecord)
    .filter((record) => record.operationType === '开启' && ['成功', '进行中'].includes(record.status))
    .forEach((record) => {
      const eventTime = parseDate(record.startTime)?.getTime()
      if (!eventTime || !timestampValues.length || eventTime < timestampValues[0] || eventTime > timestampValues[timestampValues.length - 1]) return
      const index = timestampValues.reduce((nearest, current, currentIndex) => (
        Math.abs(current - eventTime) < Math.abs(timestampValues[nearest] - eventTime) ? currentIndex : nearest
      ), 0)
      eventsByIndex.set(index, { index, label: `灌溉 ${formatDateTime(record.startTime).slice(5, 16)}` })
    })
  return {
    times: timestamps.map((value) => formatDateTime(value).slice(5, 16)),
    temperature: timestamps.map((value) => temperatureByTime.get(value) ?? null),
    soilHumidity: timestamps.map((value) => humidityByTime.get(value) ?? null),
    events: [...eventsByIndex.values()],
    threshold,
  }
}
