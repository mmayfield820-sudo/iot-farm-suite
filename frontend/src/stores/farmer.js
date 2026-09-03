import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useUserStore } from '@/stores/user'
import { farmerAlerts, farmerIrrigationRecords, farmerPlots, getFarmerTrend, weatherCurrent } from '@/mock/farmerData'
import { buildControlCommand, commandResultLabel } from '@/services/mqttProtocol'
import { getFarmList, getFarmOverview } from '@/api/platform'
import { getIrrigationRecords } from '@/api/device'
import { getPlotMetrics } from '@/api/sensor'
import { getAlertRules } from '@/api/alertRule'
import { getIrrigationSettings, updateIrrigationSettings } from '@/api/irrigationSettings'
import { acknowledgeAlert, getAlertList } from '@/api/alert'
import { createDeviceCommand, getCommandStatus } from '@/api/command'
import { getWeatherForecast } from '@/api/weather'
import { formatDateTime, metricSeriesToTrend, normalizeAlert, normalizeFarm, normalizeId, normalizeIrrigationRecord, normalizePlot, overviewMetricsToReport, unwrapList } from '@/utils/dataAdapters'

const clone = (value) => JSON.parse(JSON.stringify(value))
const isMock = import.meta.env.VITE_USE_MOCK === 'true'
const nowText = () => {
  const date = new Date(); const pad = (number) => String(number).padStart(2, '0')
  return formatDateTime(date)
}
const settledValue = (result, fallback = {}) => result?.status === 'fulfilled' ? result.value : fallback

export const useFarmerStore = defineStore('farmer', () => {
  const userStore = useUserStore()
  const plots = ref(isMock ? clone(farmerPlots) : [])
  const alerts = ref(isMock ? clone(farmerAlerts).map(normalizeAlert) : [])
  const irrigationRecords = ref(isMock ? clone(farmerIrrigationRecords).map(normalizeIrrigationRecord) : [])
  const historyByPlot = ref({})
  const weather = ref(isMock ? clone(weatherCurrent) : null)
  const commandLogs = ref([])
  const selectedPlotId = ref(normalizeId(userStore.user?.roleScopes?.farmer?.plotIds?.[0] || userStore.user?.accessiblePlots?.[0] || plots.value[0]?.plotId))
  const selectedFarmId = ref(normalizeId(plots.value[0]?.farmId))
  const loading = ref(false)
  const initialized = ref(false)
  const loadError = ref('')
  const serviceStatus = ref({ mqtt: true, realtime: true, weather: true, assistant: true })

  const scopedPlotIds = computed(() => {
    const ids = userStore.user?.roleScopes?.farmer?.plotIds || userStore.user?.accessiblePlots || []
    return ids.map(normalizeId)
  })
  const accessiblePlots = computed(() => scopedPlotIds.value.length ? plots.value.filter((plot) => scopedPlotIds.value.includes(normalizeId(plot.plotId))) : plots.value)
  const accessibleFarms = computed(() => [...new Map(accessiblePlots.value.map((plot) => [normalizeId(plot.farmId), {
    farmId: normalizeId(plot.farmId), farmName: plot.farmName || '未命名农场',
  }])).values()])
  const currentFarm = computed(() => accessibleFarms.value.find((farm) => farm.farmId === normalizeId(selectedFarmId.value)) || accessibleFarms.value[0] || null)
  const farmPlots = computed(() => accessiblePlots.value.filter((plot) => normalizeId(plot.farmId) === currentFarm.value?.farmId))
  const currentPlot = computed(() => farmPlots.value.find((plot) => normalizeId(plot.plotId) === normalizeId(selectedPlotId.value)) || farmPlots.value[0] || null)
  const accessibleIds = computed(() => accessiblePlots.value.map((plot) => normalizeId(plot.plotId)))
  const farmIds = computed(() => farmPlots.value.map((plot) => normalizeId(plot.plotId)))
  const visibleAlerts = computed(() => alerts.value.filter((alert) => accessibleIds.value.includes(normalizeId(alert.plotId))))
  const visibleRecords = computed(() => irrigationRecords.value.filter((record) => accessibleIds.value.includes(normalizeId(record.plotId))))
  const farmAlerts = computed(() => alerts.value.filter((alert) => farmIds.value.includes(normalizeId(alert.plotId))))
  const farmRecords = computed(() => irrigationRecords.value.filter((record) => farmIds.value.includes(normalizeId(record.plotId))))
  const unhandledCount = computed(() => farmAlerts.value.filter((alert) => alert.status === '未处理').length)

  async function refreshAlerts() {
    if (isMock) return
    const alertResult = await getAlertList()
    alerts.value = unwrapList(alertResult).map((row) => {
      const alert = normalizeAlert(row)
      return { ...alert, plotName: getPlot(alert.plotId)?.plotName || alert.plotName || alert.plotId }
    })
  }

  function ensureSelectedFarm() {
    if (!accessibleFarms.value.some((farm) => farm.farmId === normalizeId(selectedFarmId.value))) selectedFarmId.value = accessibleFarms.value[0]?.farmId || ''
  }
  function ensureSelectedPlot() {
    if (!farmIds.value.includes(normalizeId(selectedPlotId.value))) selectedPlotId.value = farmIds.value[0] || ''
  }
  function selectFarm(farmId) {
    const id = normalizeId(farmId)
    if (!accessibleFarms.value.some((farm) => farm.farmId === id)) return
    selectedFarmId.value = id
    const nextPlot = accessiblePlots.value.find((plot) => normalizeId(plot.farmId) === id)
    if (nextPlot) selectPlot(nextPlot.plotId)
  }
  function selectPlot(plotId) {
    const id = normalizeId(plotId)
    if (farmIds.value.includes(id)) {
      selectedPlotId.value = id
      if (!isMock) loadWeather(id)
    }
  }
  function getPlot(plotId) { return accessiblePlots.value.find((plot) => normalizeId(plot.plotId) === normalizeId(plotId)) }

  async function loadFarmerData(force = false) {
    if (initialized.value && !force) return
    if (isMock) { initialized.value = true; ensureSelectedFarm(); ensureSelectedPlot(); return }
    loading.value = true; loadError.value = ''
    try {
      const farmRows = unwrapList(await getFarmList()).map(normalizeFarm)
      const [overviewResults, ruleResult, alertResult] = await Promise.all([
        Promise.allSettled(farmRows.map((farm) => getFarmOverview(farm.farmId))),
        Promise.resolve(getAlertRules()).catch(() => []),
        Promise.resolve(getAlertList()).catch(() => []),
      ])
      const rules = unwrapList(ruleResult)
      const overviewRows = overviewResults.flatMap((result, index) => unwrapList(settledValue(result, [])).map((overview) => ({ overview, farm: farmRows[index] })))
      const plotResults = await Promise.all(overviewRows.map(async ({ overview, farm }) => {
        const row = overview.plot || {}
        const plotId = normalizeId(row.id ?? row.plotId)
        const [settingsResult, recordsResult] = await Promise.allSettled([getIrrigationSettings(plotId), getIrrigationRecords(plotId)])
        const settings = settledValue(settingsResult, {})
        const records = unwrapList(settledValue(recordsResult, [])).map(normalizeIrrigationRecord)
        const humidityRule = rules.find((rule) => normalizeId(rule.plotId) === plotId)
        const threshold = {
          threshold: Number(settings.soilMoistureThreshold ?? humidityRule?.soilMoistureThreshold ?? humidityRule?.threshold ?? 35),
          irrigationDuration: Number(settings.irrigationDuration ?? 30),
          irrigationInterval: Number(settings.irrigationInterval ?? 60),
        }
        return {
          plot: normalizePlot({ ...row, farmName: farm.name }, {
            farm,
            report: overviewMetricsToReport(overview.latestMetrics, plotId),
            threshold,
            devices: overview.devices || [],
            irrigationRecords: records,
            staleDataMinutes: 15,
          }),
          records,
        }
      }))
      const normalizedPlots = plotResults.map((item) => item.plot)
      plots.value = normalizedPlots
      alerts.value = unwrapList(alertResult).map((row) => {
        const alert = normalizeAlert(row)
        return { ...alert, plotName: normalizedPlots.find((plot) => normalizeId(plot.plotId) === alert.plotId)?.plotName || alert.plotName || alert.plotId }
      })
      irrigationRecords.value = plotResults.flatMap((item) => item.records)
      initialized.value = true
      ensureSelectedFarm()
      ensureSelectedPlot()
      await loadWeather(selectedPlotId.value)
    } catch (error) {
      loadError.value = error?.response?.data?.message || error.message || '农户数据加载失败'
      throw error
    } finally { loading.value = false }
  }

  async function refreshRealtimeData() {
    if (isMock || !plots.value.length) return
    const farmRows = [...new Map(plots.value.map((plot) => [normalizeId(plot.farmId), {
      farmId: normalizeId(plot.farmId), name: plot.farmName,
    }])).values()]
    const overviewResults = await Promise.allSettled(farmRows.map((farm) => getFarmOverview(farm.farmId)))
    overviewResults.forEach((result, index) => {
      if (result.status !== 'fulfilled') return
      const farm = farmRows[index]
      unwrapList(result.value).forEach((overview) => {
        const row = overview.plot || {}
        const plotId = normalizeId(row.id ?? row.plotId)
        const existing = getPlot(plotId)
        if (!existing) return
        const refreshed = normalizePlot({ ...row, farmName: farm.name }, {
          farm,
          report: overviewMetricsToReport(overview.latestMetrics, plotId),
          threshold: {
            threshold: existing.threshold,
            irrigationDuration: existing.irrigationDuration,
            irrigationInterval: existing.irrigationInterval,
          },
          devices: overview.devices || [],
          irrigationRecords: irrigationRecords.value.filter((record) => normalizeId(record.plotId) === plotId),
          staleDataMinutes: 15,
        })
        Object.assign(existing, refreshed)
      })
    })
  }

  async function refreshIrrigationRecords(plotId = selectedPlotId.value) {
    if (isMock || !plotId) return
    const normalizedPlotId = normalizeId(plotId)
    const records = unwrapList(await getIrrigationRecords(normalizedPlotId)).map(normalizeIrrigationRecord)
    irrigationRecords.value = [
      ...irrigationRecords.value.filter((record) => normalizeId(record.plotId) !== normalizedPlotId),
      ...records,
    ]
    const current = getPlot(normalizedPlotId)
    if (!current) return
    const latestSuccessful = records.find((record) => record.status === '成功' && ['开启', '关闭'].includes(record.operationType))
    const switchState = current.devices?.irrigation?.switchState
    current.irrigating = switchState === 'on'
      ? true
      : switchState === 'off'
        ? false
        : latestSuccessful?.operationType === '开启'
    current.status = current.irrigating ? 'irrigating' : (current.humidity < current.threshold ? 'alert' : 'normal')
  }

  async function loadWeather(plotId = selectedPlotId.value) {
    if (isMock || !plotId) return
    try {
      const response = await getWeatherForecast({ plotId })
      const body = response?.data || response || {}
      const current = body.current || body.currentWeather || body.current_weather || body
      weather.value = {
        ...current,
        hourly: Array.isArray(body.hourly) ? body.hourly : [],
        daily: Array.isArray(body.daily) ? body.daily : [],
        city: current.city || current.location || body.city || '',
        condition: current.condition || current.weather || '',
        temperature: Number(current.temperature ?? current.temp ?? 0),
        high: Number(current.high ?? current.max_temperature ?? 0),
        low: Number(current.low ?? current.min_temperature ?? 0),
        rainProbability: Number(current.rainProbability ?? current.rain_probability ?? current.precipitation_probability ?? 0),
        updatedAt: current.updatedAt || current.updated_at || '',
      }
      serviceStatus.value.weather = true
    } catch {
      weather.value = null
      serviceStatus.value.weather = false
    }
  }

  function getTrend(plotId, period = '24h') {
    const plot = getPlot(plotId)
    if (isMock) return { ...getFarmerTrend(plotId, period), threshold: plot?.threshold ?? 35 }
    return historyByPlot.value[normalizeId(plotId)] || { times: [], temperature: [], soilHumidity: [], events: [], threshold: plot?.threshold ?? 35 }
  }
  async function loadHistory(plotId, period = '24h', dateRange = []) {
    if (!plotId) return
    if (isMock) return
    const to = period === 'custom' ? dateRange[1] : new Date()
    const hours = period === '30d' ? 30 * 24 : period === '7d' ? 7 * 24 : 24
    const from = period === 'custom' ? dateRange[0] : new Date(to.getTime() - hours * 60 * 60 * 1000)
    const params = { from: from.toISOString(), to: to.toISOString() }
    const [temperature, humidity] = await Promise.all([
      getPlotMetrics(plotId, { ...params, type: 'temperature' }),
      getPlotMetrics(plotId, { ...params, type: 'humidity' }),
    ])
    historyByPlot.value[normalizeId(plotId)] = metricSeriesToTrend(unwrapList(temperature), unwrapList(humidity), getPlot(plotId)?.threshold ?? 35)
  }

  async function updateThreshold(plotId, config) {
    const plot = getPlot(plotId)
    if (!plot) throw new Error('无权访问该地块或地块不存在')
    if (!isMock) await updateIrrigationSettings(plotId, {
      soilMoistureThreshold: config.threshold,
      irrigationDuration: config.irrigationDuration,
      irrigationInterval: config.irrigationInterval,
    })
    Object.assign(plot, { threshold: config.threshold, irrigationDuration: config.irrigationDuration, irrigationInterval: config.irrigationInterval, maxDuration: config.irrigationDuration })
    await refreshAlerts()
  }

  async function acknowledge(alertId) {
    const alert = visibleAlerts.value.find((item) => normalizeId(item.alertId) === normalizeId(alertId))
    if (!alert) throw new Error('告警不存在或无权处理')
    if (!isMock) await acknowledgeAlert(alertId)
    alert.status = '处理中'
    alert.handledBy = userStore.user?.id || ''
    alert.handledAt = nowText()
  }

  function finishControl(plotId, action, status = '成功', source = '手动') {
    const plot = getPlot(plotId)
    if (!plot) return
    const opening = action === 'open'
    if (status === '成功') {
      plot.irrigating = opening
      plot.status = opening ? 'irrigating' : (plot.humidity < plot.threshold ? 'alert' : 'normal')
      if (!opening) {
        const activeRecord = irrigationRecords.value.find((record) => normalizeId(record.plotId) === normalizeId(plotId) && record.status === '进行中')
        if (activeRecord) {
          activeRecord.endTime = nowText()
          const start = new Date(activeRecord.startTime.replace(' ', 'T'))
          activeRecord.duration = Number.isNaN(start.getTime()) ? '-' : Math.max(0, Math.round((Date.now() - start.getTime()) / 60000))
          activeRecord.status = '成功'
        }
      }
    }
    irrigationRecords.value.unshift(normalizeIrrigationRecord({
      recordId: `IR${Date.now()}`, plotId, plotName: plot.plotName, deviceId: plot.devices?.irrigation?.deviceId || plot.valveId,
      operatorId: userStore.user?.id, operator: userStore.user?.displayName || userStore.user?.employeeNo,
      operationType: opening ? '开启' : '关闭', activationType: source,
      startTime: nowText(), endTime: opening && status === '成功' ? '' : nowText(), duration: opening && status === '成功' ? '-' : 0,
      status: opening && status === '成功' ? '进行中' : status,
    }))
  }

  function beginCommand(plotId, action, durationMinutes = null, activationType = 'manual') {
    const plot = getPlot(plotId)
    const device = plot?.devices?.irrigation
    if (!plot || !device?.deviceNo) throw new Error('当前地块未绑定可用的灌溉控制器')
    if (!device.online && !isMock) throw new Error('灌溉控制器离线，无法下发指令')
    const mqttDeviceId = device.deviceUuid || device.mqttId || device.deviceNo
    const built = buildControlCommand(mqttDeviceId, action)
    const command = {
      commandId: built.commandId,
      plotId: normalizeId(plotId),
      deviceId: device.deviceId || device.id || device.deviceNo,
      topic: built.topic,
      action: action === 'open' ? 'irrigation_on' : 'irrigation_off',
      durationMinutes: action === 'open' ? durationMinutes : null,
      activationType,
      payload: built.payload,
      status: '下发中',
      sentAt: nowText(),
      resultAt: '',
    }
    commandLogs.value.unshift(command)
    return command
  }

  async function sendControl(command) {
    if (isMock) return { result: 'success' }
    let response = await createDeviceCommand(command.deviceId, command.action, command.durationMinutes, command.activationType)
    response = response?.data || response
    if (response.commandId) {
      const sequence = Number(response.commandId)
      command.commandId = response.commandId
      command.payload = {
        ...command.payload,
        seq: Number.isInteger(sequence) ? sequence : command.payload.seq,
      }
    }
    if (response.status === 'pending' && response.commandId) command.status = '等待设备响应'
    return response
  }

  async function waitCommandResult(commandId, timeoutMs = 36000, pollMs = 1000) {
    if (isMock) return { status: 'success' }
    const deadline = Date.now() + timeoutMs
    let latest = { commandId, status: 'pending' }
    while (Date.now() < deadline) {
      const response = await getCommandStatus(commandId)
      latest = response?.data || response || latest
      if (['success', 'failed', 'timeout'].includes(latest.status)) return latest
      await new Promise((resolve) => setTimeout(resolve, pollMs))
    }
    return { ...latest, status: 'timeout', message: '设备响应超时' }
  }

  function completeCommand(commandId, result = 'success', source = '手动') {
    const command = commandLogs.value.find((item) => item.commandId === commandId)
    if (!command) return
    const nextStatus = commandResultLabel(result)
    command.status = nextStatus === '未知' ? '失败' : nextStatus
    command.resultAt = nowText()
    if (command.status === '成功') {
      finishControl(command.plotId, command.action === 'irrigation_on' ? 'open' : 'close', command.status, source)
    }
  }

  return { plots, alerts, irrigationRecords, historyByPlot, commandLogs, weather, selectedPlotId, selectedFarmId, serviceStatus, loading, initialized, loadError, accessiblePlots, accessibleFarms, currentFarm, farmPlots, currentPlot, visibleAlerts, visibleRecords, farmAlerts, farmRecords, unhandledCount, loadFarmerData, refreshRealtimeData, refreshIrrigationRecords, loadHistory, loadWeather, refreshAlerts, selectFarm, selectPlot, getPlot, getTrend, updateThreshold, acknowledge, finishControl, beginCommand, sendControl, waitCommandResult, completeCommand }
})
