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
  const pad = (number) => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function isHeartbeatOnline(active, lastHeartbeat, offlineMinutes = 30) {
  if (active === false || active === 0) return false
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
    createdAt: firstDefined(row.createdAt, row.created_at, ''),
  }
}

export function normalizeDevice(row = {}, options = {}) {
  const active = Boolean(firstDefined(row.active, row.Active, row.status !== '停用', true))
  const lastHeartbeat = firstDefined(row.lastHeartbeat, row.last_heartbeat, '')
  const statusOnline = row.status === undefined || row.status === null ? undefined : row.status === '在线'
  const online = firstDefined(row.online, row.deviceOnline, statusOnline, isHeartbeatOnline(active, lastHeartbeat, options.offlineMinutes))
  const type = firstDefined(row.type, row.deviceType, row.device_type, '未知设备')
  const plotId = normalizeId(firstDefined(row.plotId, row.plot_id, row.plotNo))
  return {
    ...row,
    id: normalizeId(firstDefined(row.id, row.deviceId, row.device_id)),
    deviceId: normalizeId(firstDefined(row.deviceId, row.device_id, row.id)),
    plotId,
    plotNo: plotId,
    deviceNo: firstDefined(row.deviceNo, row.deviceCode, row.device_code, ''),
    type,
    active,
    online: Boolean(online),
    status: !active ? '停用' : online ? '在线' : '离线',
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
  const startTime = firstDefined(row.startTime, row.start_time, '')
  const endTime = firstDefined(row.endTime, row.end_time, '')
  const start = parseDate(startTime)
  const end = parseDate(endTime)
  const statusMap = { 执行中: '进行中' }
  return {
    ...row,
    recordId: normalizeId(firstDefined(row.recordId, row.record_id, row.id)),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id)),
    deviceId: normalizeId(firstDefined(row.deviceId, row.device_id)),
    operationType: firstDefined(row.operationType, row.actionType, row.action_type, ''),
    activationType: firstDefined(row.activationType, row.activation_type, row.source, '手动'),
    operatorId: normalizeId(firstDefined(row.operatorId, row.operator_id)),
    operator: firstDefined(row.operator, row.operatorName, row.operator_name, row.operatorUsername, '系统'),
    startTime,
    endTime,
    duration: firstDefined(row.duration, start && end ? Math.max(0, Math.round((end - start) / 60000)) : '-'),
    status: statusMap[row.status] || firstDefined(row.status, '失败'),
    source: firstDefined(row.source, row.activationType, row.activation_type, '手动'),
  }
}

export function normalizeAlert(row = {}) {
  const statusMap = { 已确认: '处理中', 已恢复: '已处理' }
  return {
    ...row,
    alertId: normalizeId(firstDefined(row.alertId, row.alert_id, row.id)),
    plotId: normalizeId(firstDefined(row.plotId, row.plot_id, row.plotNo)),
    deviceId: normalizeId(firstDefined(row.deviceId, row.device_id)),
    type: firstDefined(row.type, row.alertType, row.alert_type, '未知告警'),
    reason: firstDefined(row.reason, row.alertDescription, row.alert_description, '暂无告警说明'),
    value: firstDefined(row.value, row.triggerValue, row.alertValue, row.alert_value, '-'),
    threshold: firstDefined(row.threshold, row.alertThreshold, row.alert_threshold, '-'),
    occurTime: firstDefined(row.occurTime, row.alertDatetime, row.alert_datetime, ''),
    status: statusMap[row.status] || statusMap[row.alert_status] || firstDefined(row.status, row.alert_status, '未处理'),
    handledBy: normalizeId(firstDefined(row.handledBy, row.handled_by)),
    handledAt: firstDefined(row.handledAt, row.handled_at, ''),
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
  const activeIrrigation = irrigationRecords.find((item) => item.operationType === '开启' && item.status === '进行中')
  const lastIrrigation = irrigationRecords.find((item) => item.operationType === '开启')
  const activeDevices = devices.filter((item) => item.active)
  const allOnline = activeDevices.length > 0 && activeDevices.every((item) => item.online)
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
    cropName: firstDefined(row.cropName, row.crop_name, '暂未种植'),
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
    dataState: row.dataState || (report.createdAt && isHeartbeatOnline(true, report.createdAt, related.staleDataMinutes || 15) ? 'realtime' : 'delayed'),
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
