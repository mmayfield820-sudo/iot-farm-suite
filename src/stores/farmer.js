import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useUserStore } from '@/stores/user'
import { farmerAlerts, farmerIrrigationRecords, farmerPlots, getFarmerTrend, weatherCurrent } from '@/mock/farmerData'
import { buildControlCommand, commandResultLabel } from '@/services/mqttProtocol'
import { getPlotDetail, getPlotList } from '@/api/plot'
import { getDeviceStatus, getIrrigationRecords } from '@/api/device'
import { getLatestSensorData, getSensorHistory } from '@/api/sensor'
import { getThresholdConfig, updateThresholdConfig } from '@/api/threshold'
import { getAlertList, confirmAlert as confirmAlertApi, resolveAlert as resolveAlertApi } from '@/api/alert'
import { controlIrrigation } from '@/api/irrigation'
import { getWeatherForecast } from '@/api/weather'
import { normalizeAlert, normalizeId, normalizeIrrigationRecord, normalizePlot, reportsToTrend, unwrapList } from '@/utils/dataAdapters'

const clone = (value) => JSON.parse(JSON.stringify(value))
const isMock = import.meta.env.VITE_USE_MOCK === 'true'
const nowText = () => {
  const date = new Date(); const pad = (number) => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
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
  const loading = ref(false)
  const initialized = ref(false)
  const loadError = ref('')
  const serviceStatus = ref({ mqtt: true, realtime: true, weather: true, assistant: true })

  const scopedPlotIds = computed(() => {
    const ids = userStore.user?.roleScopes?.farmer?.plotIds || userStore.user?.accessiblePlots || []
    return ids.map(normalizeId)
  })
  const accessiblePlots = computed(() => plots.value.filter((plot) => scopedPlotIds.value.includes(normalizeId(plot.plotId))))
  const currentPlot = computed(() => accessiblePlots.value.find((plot) => normalizeId(plot.plotId) === normalizeId(selectedPlotId.value)) || accessiblePlots.value[0] || null)
  const accessibleIds = computed(() => accessiblePlots.value.map((plot) => normalizeId(plot.plotId)))
  const visibleAlerts = computed(() => alerts.value.filter((alert) => accessibleIds.value.includes(normalizeId(alert.plotId))))
  const visibleRecords = computed(() => irrigationRecords.value.filter((record) => accessibleIds.value.includes(normalizeId(record.plotId))))
  const unhandledCount = computed(() => visibleAlerts.value.filter((alert) => alert.status === '未处理').length)

  function ensureSelectedPlot() {
    if (!accessibleIds.value.includes(normalizeId(selectedPlotId.value))) selectedPlotId.value = accessibleIds.value[0] || ''
  }
  function selectPlot(plotId) {
    const id = normalizeId(plotId)
    if (accessibleIds.value.includes(id)) {
      selectedPlotId.value = id
      if (!isMock) loadWeather(id)
    }
  }
  function getPlot(plotId) { return accessiblePlots.value.find((plot) => normalizeId(plot.plotId) === normalizeId(plotId)) }

  async function loadFarmerData(force = false) {
    if (initialized.value && !force) return
    if (isMock) { initialized.value = true; ensureSelectedPlot(); return }
    loading.value = true; loadError.value = ''
    try {
      const plotResponse = await getPlotList()
      const plotRows = unwrapList(plotResponse)
      const normalizedPlots = await Promise.all(plotRows.map(async (row) => {
        const plotId = normalizeId(row.plotId ?? row.plot_id ?? row.id)
        const results = await Promise.allSettled([
          getPlotDetail(plotId), getLatestSensorData(plotId), getThresholdConfig(plotId), getDeviceStatus(plotId), getIrrigationRecords(plotId),
        ])
        const detail = settledValue(results[0], {})
        const report = settledValue(results[1], {})
        const threshold = settledValue(results[2], {})
        const deviceResponse = settledValue(results[3], [])
        const recordResponse = settledValue(results[4], [])
        const records = unwrapList(recordResponse).map(normalizeIrrigationRecord)
        return normalizePlot({ ...row, ...(detail?.data || detail) }, {
          report: report?.data || report,
          threshold: threshold?.data || threshold,
          devices: unwrapList(deviceResponse),
          irrigationRecords: records,
          staleDataMinutes: 15,
        })
      }))
      plots.value = normalizedPlots
      const [alertResult, ...recordResults] = await Promise.allSettled([
        getAlertList(), ...normalizedPlots.map((plot) => getIrrigationRecords(plot.plotId)),
      ])
      alerts.value = unwrapList(settledValue(alertResult, [])).map((row) => {
        const alert = normalizeAlert(row)
        return { ...alert, plotName: normalizedPlots.find((plot) => normalizeId(plot.plotId) === alert.plotId)?.plotName || alert.plotName || alert.plotId }
      })
      irrigationRecords.value = recordResults.flatMap((result) => unwrapList(settledValue(result, [])).map(normalizeIrrigationRecord))
      initialized.value = true
      ensureSelectedPlot()
      await loadWeather(selectedPlotId.value)
    } catch (error) {
      loadError.value = error?.response?.data?.message || error.message || '农户数据加载失败'
      throw error
    } finally { loading.value = false }
  }

  async function loadWeather(plotId = selectedPlotId.value) {
    if (isMock || !plotId) return
    try {
      const response = await getWeatherForecast({ plotId })
      const body = response?.data || response || {}
      const current = body.current || body.currentWeather || body.current_weather || body
      weather.value = {
        ...current,
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
    const params = { plotId, period }
    if (period === 'custom' && dateRange?.length === 2) {
      params.startTime = dateRange[0].toISOString()
      params.endTime = dateRange[1].toISOString()
    }
    const response = await getSensorHistory(params)
    historyByPlot.value[normalizeId(plotId)] = reportsToTrend(unwrapList(response), getPlot(plotId)?.threshold ?? 35)
  }

  async function updateThreshold(plotId, config) {
    const plot = getPlot(plotId)
    if (!plot) throw new Error('无权访问该地块或地块不存在')
    const payload = {
      soil_moisture_threshold: config.threshold,
      irrigation_length_minutes: config.irrigationDuration,
      irrigation_interval_minutes: config.irrigationInterval,
    }
    if (!isMock) await updateThresholdConfig(plotId, payload)
    Object.assign(plot, { threshold: config.threshold, irrigationDuration: config.irrigationDuration, irrigationInterval: config.irrigationInterval, maxDuration: config.irrigationDuration })
  }

  async function updateAlert(alertId, status) {
    const alert = visibleAlerts.value.find((item) => normalizeId(item.alertId) === normalizeId(alertId))
    if (!alert) throw new Error('告警不存在或无权处理')
    if (!isMock) {
      if (status === '处理中') await confirmAlertApi(alertId)
      else if (status === '已处理') await resolveAlertApi(alertId)
    }
    alert.status = status
    if (status === '已处理') { alert.handledBy = userStore.user?.id || ''; alert.handledAt = nowText() }
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
      operatorId: userStore.user?.id, operator: userStore.user?.displayName || userStore.user?.username,
      operationType: opening ? '开启' : '关闭', activationType: source,
      startTime: nowText(), endTime: opening && status === '成功' ? '' : nowText(), duration: opening && status === '成功' ? '-' : 0,
      status: opening && status === '成功' ? '进行中' : status,
    }))
  }

  function beginCommand(plotId, action) {
    const plot = getPlot(plotId)
    const device = plot?.devices?.irrigation
    if (!plot || !device?.deviceNo) throw new Error('当前地块未绑定可用的灌溉控制器')
    if (!device.online && !isMock) throw new Error('灌溉控制器离线，无法下发指令')
    const built = buildControlCommand(device.deviceNo, action)
    const command = { commandId: built.payload.commandId, plotId: normalizeId(plotId), deviceId: device.deviceId || device.deviceNo, topic: built.topic, action: built.payload.action, payload: built.payload, status: '下发中', sentAt: nowText(), resultAt: '' }
    commandLogs.value.unshift(command)
    return command
  }

  async function sendControl(command, duration) {
    if (isMock) return { result: 'success' }
    const response = await controlIrrigation({
      plot_id: command.plotId,
      device_id: command.deviceId,
      action_type: command.action === 'irrigation_on' ? '开启' : '关闭',
      activation_type: '手动',
      irrigation_length_minutes: command.action === 'irrigation_on' ? duration : undefined,
      command_id: command.commandId,
    })
    return response?.data || response
  }

  function completeCommand(commandId, result = 'success', source = '手动') {
    const command = commandLogs.value.find((item) => item.commandId === commandId)
    if (!command) return
    const nextStatus = commandResultLabel(result)
    command.status = nextStatus === '未知' ? '失败' : nextStatus
    command.resultAt = nowText()
    finishControl(command.plotId, command.action === 'irrigation_on' ? 'open' : 'close', command.status, source)
  }

  return { plots, alerts, irrigationRecords, historyByPlot, commandLogs, weather, selectedPlotId, serviceStatus, loading, initialized, loadError, accessiblePlots, currentPlot, visibleAlerts, visibleRecords, unhandledCount, loadFarmerData, loadHistory, loadWeather, selectPlot, getPlot, getTrend, updateThreshold, updateAlert, finishControl, beginCommand, sendControl, completeCommand }
})
