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
  const status = firstDefined(row.status, row.farmStatus, row.farm_status, row.active === false || row.Active === false ? 'inactive' : 'active')
  return {
    ...row,
    farmId: normalizeId(firstDefined(row.farmId, row.farm_id, row.id)),
    name: firstDefined(row.name, row.farmName, row.farm_name, '未命名农场'),
    farmName: firstDefined(row.farmName, row.farm_name, row.name, '未命名农场'),
    province: firstDefined(row.province, ''),
    city: firstDefined(row.city, ''),
    address: firstDefined(row.address, row.location, ''),
    areaMu: firstDefined(row.areaMu, row.area_mu, null),
    managerEmployeeNo: firstDefined(row.managerEmployeeNo, row.manager_employee_no, ''),
    managerName: firstDefined(row.managerName, row.manager_name, ''),
    note: firstDefined(row.note, ''),
    status,
    active: status === 'active',
    createdAt: firstDefined(row.createdAt, row.created_at, ''),
    updatedAt: firstDefined(row.updatedAt, row.updated_at, ''),
  }
}

export function normalizeDevice(row = {}, options = {}) {
  const typeMap = { temperature: '温度传感器', humidity: '湿度传感器', irrigation: '灌溉设备' }
  const lastHeartbeat = firstDefined(row.lastHeartbeat, row.last_heartbeat, row.lastSeenAt, row.last_seen_at, '')
  const statusOnline = row.status === undefined || row.status === null ? undefined : ['online', '在线'].includes(row.status)
  const online = firstDefined(row.online, row.deviceOnline, statusOnline, isHeartbeatOnline(lastHeartbeat, options.offlineMinutes))
  const rawType = firstDefined(row.type, row.deviceType, row.device_type, '未知设备')
  const type = typeMap[rawType] || rawType
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
    switchState: firstDefined(row.switchState, row.switch_state, null),
    switchChangedAt: firstDefined(row.switchChangedAt, row.switch_changed_at, ''),
    lastHeartbeat,
    createdAt: firstDefined(row.createdAt, row.created_at, ''),
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
    updatedAt: firstDefined(row.updatedAt, row.updated_at, ''),
  }
}

export function normalizeReport(row = {}) {
  return {
    reportId: normalizeId(firstDefined(row.reportId, row.report_id, row.id)),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id)),
    humidity: Number(firstDefined(row.humidity, row.plotMoisture, row.plot_moisture, 0)),
    temperature: Number(firstDefined(row.temperature, 0)),
    createdAt: firstDefined(row.createdAt, row.created_at, row.updateTime, ''),
  }
}

export function normalizeIrrigationRecord(row = {}) {
  const startTime = firstDefined(row.startTime, row.start_time, row.requestedAt, row.requested_at, '')
  const endTime = firstDefined(row.endTime, row.end_time, row.executedAt, row.executed_at, '')
  const start = parseDate(startTime)
  const end = parseDate(endTime)
  const statusMap = { pending: '待确认', success: '成功', failed: '失败', timeout: '超时', 执行中: '进行中' }
  const actionMap = { irrigation_on: '开启', irrigation_off: '关闭', on: '开启', off: '关闭' }
  return {
    ...row,
    recordId: normalizeId(firstDefined(row.recordId, row.record_id, row.id)),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id)),
    deviceId: normalizeId(firstDefined(row.deviceId, row.device_id)),
    operationType: actionMap[firstDefined(row.operationType, row.action, row.actionType, row.action_type, '')] || firstDefined(row.operationType, row.action, row.actionType, row.action_type, ''),
    activationType: firstDefined(row.activationType, row.activation_type, row.source, '手动'),
    operatorId: normalizeId(firstDefined(row.operatorId, row.operator_id)),
    operator: firstDefined(row.operator, row.operatorName, row.operator_name, row.operatorEmployeeNo, '系统'),
    startTime,
    endTime,
    duration: firstDefined(row.duration, start && end ? Math.max(0, Math.round((end - start) / 60000)) : '-'),
    status: statusMap[row.status] || firstDefined(row.status, '失败'),
    source: firstDefined(row.source, row.activationType, row.activation_type, '手动'),
  }
}

export function normalizeAlert(row = {}) {
  const statusMap = { active: '未处理', acknowledged: '处理中', recovered: '已处理', 已确认: '处理中', 已恢复: '已处理' }
  const rawType = firstDefined(row.type, row.metricType, row.metric_type, row.alertType, row.alert_type, '未知告警')
  const typeMap = {
    humidity: '湿度过低',
    temperature: '温度异常',
    low_moisture: '湿度过低',
    high_moisture: '湿度偏高',
    device_offline: '设备离线',
    device_fault: '设备故障',
    irrigation_failed: '灌溉失败',
  }
  const occurTime = firstDefined(row.occurTime, row.triggeredAt, row.triggered_at, row.alertDatetime, row.alert_datetime, '')
  const handledAt = firstDefined(row.handledAt, row.handled_at, '')
  const value = firstDefined(row.value, row.triggerValue, row.alertValue, row.alert_value, '-')
  const threshold = firstDefined(row.threshold, row.alertThreshold, row.alert_threshold, '-')
  const rawReason = firstDefined(row.reason, row.description, row.alertDescription, row.alert_description, '')
  const reason = rawReason && !/^\?+$/.test(String(rawReason).replace(/[^?]/g, '')) ? rawReason : ({
    low_moisture: `当前湿度 ${value}%，低于阈值 ${threshold}%`,
    high_moisture: `当前湿度 ${value}%，高于阈值 ${threshold}%`,
    device_offline: '设备已离线，请检查设备连接状态',
    device_fault: '设备状态异常，请及时检查',
    irrigation_failed: '灌溉执行失败，请检查设备状态',
  }[rawType] || '请查看告警详情并及时处理')
  return {
    ...row,
    alertId: normalizeId(firstDefined(row.alertId, row.alert_id, row.id)),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id, row.plotNo)),
    deviceId: normalizeId(firstDefined(row.deviceId, row.device_id)),
    typeCode: rawType,
    type: typeMap[rawType] || rawType,
    reason,
    value,
    threshold,
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
  const irrigationRecords = (related.irrigationRecords || row.irrigationRecords || []).map(normalizeIrrigationRecord).sort((a, b) => (parseDate(b.startTime)?.getTime() || 0) - (parseDate(a.startTime)?.getTime() || 0))
  const alerts = (related.alerts || row.alerts || []).map(normalizeAlert)
  const deviceByType = {
    temperature: devices.find((item) => item.type.includes('温度')),
    humidity: devices.find((item) => item.type.includes('湿度')),
    irrigation: devices.find((item) => item.type.includes('灌溉')),
  }
  const reportedIrrigationState = deviceByType.irrigation?.switchState
  const recordIrrigationState = irrigationRecords.find((item) => item.operationType === '开启' && item.status === '进行中')
    || (irrigationRecords.find((item) => ['开启', '关闭'].includes(item.operationType) && item.status === '成功')?.operationType === '开启')
  const activeIrrigation = reportedIrrigationState === 'on'
    ? true
    : reportedIrrigationState === 'off'
      ? false
      : Boolean(recordIrrigationState)
  const lastIrrigation = irrigationRecords.find((item) => item.operationType === '开启')
  const allOnline = devices.length > 0 && devices.every((item) => item.online)
  const plotId = normalizeId(firstDefined(row.plotId, row.plot_id, row.id))
  const humidity = Number(firstDefined(row.humidity, report.humidity, 0))
  const status = !allOnline ? 'offline' : activeIrrigation ? 'irrigating' : humidity < threshold.threshold ? 'alert' : 'normal'
  const heartbeatTimes = devices.map((item) => parseDate(item.lastHeartbeat)).filter(Boolean).sort((a, b) => b - a)
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
    deviceCount: devices.length,
    dataState: row.dataState || (report.createdAt && isHeartbeatOnline(report.createdAt, related.staleDataMinutes || 15) ? 'realtime' : 'delayed'),
    irrigating: Boolean(activeIrrigation || row.irrigating),
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
  const reports = rows.map(normalizeReport).sort((a, b) => (parseDate(a.createdAt)?.getTime() || 0) - (parseDate(b.createdAt)?.getTime() || 0))
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

export function metricSeriesToTrend(temperatureRows = [], humidityRows = [], threshold = 35) {
  const temperatureByTime = new Map(temperatureRows.map((item) => [item.ts, Number(item.value)]))
  const humidityByTime = new Map(humidityRows.map((item) => [item.ts, Number(item.value)]))
  const timestamps = [...new Set([...temperatureByTime.keys(), ...humidityByTime.keys()])]
    .filter((value) => parseDate(value))
    .sort((a, b) => parseDate(a) - parseDate(b))
  return {
    times: timestamps.map((value) => formatDateTime(value).slice(5, 16)),
    temperature: timestamps.map((value) => temperatureByTime.get(value) ?? null),
    soilHumidity: timestamps.map((value) => humidityByTime.get(value) ?? null),
    events: [],
    threshold,
  }
}
