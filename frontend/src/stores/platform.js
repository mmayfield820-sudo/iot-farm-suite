import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { initialSystemParams, platformAlerts, platformAuditLogs, platformDevices, platformFarms, platformPlots, platformUsers } from '@/mock/platformData'
import { acknowledgeAlert } from '@/api/alert'
import { bindDevice as bindDeviceApi, createDevice, getAllDevices, getFarmList, getFarmOverview, getUserList, resetUserPassword, saveUser as saveUserApi, unbindDevice as unbindDeviceApi, updateUserActive } from '@/api/platform'
import { normalizeAlert, normalizeDevice, normalizeFarm, normalizeId, normalizePlot, overviewMetricsToReport, unwrapList } from '@/utils/dataAdapters'

const clone = (value) => JSON.parse(JSON.stringify(value))
const isMock = import.meta.env.VITE_USE_MOCK === 'true'
const timeText = () => new Date().toLocaleString('zh-CN', { hour12: false })
const roleLabel = { farmer: '农户', farmAdmin: '农场管理员', farm_admin: '农场管理员', systemAdmin: '系统管理员', system_admin: '系统管理员' }
const roleCode = { 农户: 'farmer', 农场管理员: 'farm_admin', 系统管理员: 'system_admin', farmer: 'farmer', farmAdmin: 'farm_admin', systemAdmin: 'system_admin' }
const deviceTypeCode = { 温度传感器: 'temperature', 湿度传感器: 'humidity', 灌溉设备: 'irrigation' }
const asArray = (value) => Array.isArray(value) ? value : typeof value === 'string' ? value.split(',').map((item) => item.trim()).filter(Boolean) : []

const normalizePlatformPlot = (row = {}) => ({
  ...row,
  internalId: normalizeId(row.internalId ?? row.plot_id ?? row.plotId ?? row.id),
  plotNo: normalizeId(row.plotNo ?? row.plot_id ?? row.plotId ?? row.id),
  farmId: normalizeId(row.farmId ?? row.farm_id),
  name: row.name || row.plotName || row.plot_name || '未命名地块',
  crop: row.crop || row.cropName || row.crop_name || '暂未种植',
  note: row.note || row.description || '',
  location: row.location || '',
  active: row.active ?? row.Active ?? true,
})
const normalizePlatformUser = (row = {}) => {
  const rawRoles = asArray(row.roles || row.roleList || row.role_list)
  const roles = rawRoles.map((item) => item?.roleName || item?.role_name || roleLabel[item?.roleCode || item?.role_code || item] || item).filter(Boolean)
  const activeAssignment = (item) => item?.active !== false && item?.Active !== false && (!item?.expiresAt && !item?.expires_at || new Date(item.expiresAt || item.expires_at).getTime() > Date.now())
  const farmIds = asArray(row.farmIds || row.farm_ids || row.userFarmRoles || row.user_farm_roles).filter(activeAssignment).map((item) => normalizeId(item?.farmId ?? item?.farm_id ?? item))
  const plotIds = asArray(row.plotIds || row.plot_ids || row.userPlotRoles || row.user_plot_roles).filter(activeAssignment).map((item) => normalizeId(item?.plotId ?? item?.plot_id ?? item))
  return {
    ...row,
    id: normalizeId(row.id ?? row.userId ?? row.user_id),
    username: row.username || '',
    name: row.name || row.displayName || row.display_name || row.username || '',
    email: row.email || '',
    phone: row.phone || '',
    roles,
    farmScope: farmIds.join(', ') || '-',
    plotScope: plotIds.join(', ') || '-',
    lastLogin: row.lastLogin || row.last_login || '-',
    status: row.active === false || row.Active === false ? '禁用' : row.status || '正常',
  }
}

export const usePlatformStore = defineStore('platform', () => {
  const farms = ref(isMock ? clone(platformFarms) : [])
  const plots = ref(isMock ? clone(platformPlots) : [])
  const devices = ref(isMock ? clone(platformDevices) : [])
  const users = ref(isMock ? clone(platformUsers) : [])
  const alerts = ref(isMock ? clone(platformAlerts) : [])
  const auditLogs = ref(isMock ? clone(platformAuditLogs) : [])
  const params = ref(clone(initialSystemParams))
  const loading = ref(false)
  const initialized = ref(false)
  const loadError = ref('')
  const capabilities = { auditLogs: isMock, systemSettings: isMock }
  const onlineDevices = computed(() => devices.value.filter((item) => item.status === '在线').length)
  const offlineDevices = computed(() => devices.value.filter((item) => ['离线', '异常'].includes(item.status)).length)
  const unhandledAlerts = computed(() => alerts.value.filter((item) => item.status === '未处理').length)
  const commandSuccessRate = ref(96.8)

  async function loadData(force = false) {
    if (initialized.value && !force) return
    if (isMock) { initialized.value = true; return }
    loading.value = true; loadError.value = ''
    try {
      const farmResponse = await getFarmList()
      farms.value = unwrapList(farmResponse).map(normalizeFarm)
      const results = await Promise.allSettled([Promise.allSettled(farms.value.map((farm) => getFarmOverview(farm.farmId))), getAllDevices(), getUserList(), getAlertList()])
      const [overviewResult, deviceResult, userResult, alertResult] = results
      if (overviewResult.status === 'fulfilled') {
        plots.value = overviewResult.value.flatMap((result, index) => unwrapList(result.status === 'fulfilled' ? result.value : []).map((overview) => {
          const base = normalizePlatformPlot(overview.plot || {})
          const normalized = normalizePlot({ ...(overview.plot || {}), farmName: farms.value[index]?.name }, {
            farm: farms.value[index], report: overviewMetricsToReport(overview.latestMetrics, base.plotNo), devices: overview.devices || [],
          })
          return { ...base, ...normalized, plotNo: normalized.plotId, name: normalized.plotName }
        }))
      }
      if (deviceResult.status === 'fulfilled') devices.value = unwrapList(deviceResult.value).map(normalizeDevice).map((device) => {
        const plot = plots.value.find((item) => item.plotNo === device.plotId)
        return { ...device, farmId: plot?.farmId || '' }
      })
      if (userResult.status === 'fulfilled') users.value = unwrapList(userResult.value).map(normalizePlatformUser)
      if (alertResult.status === 'fulfilled') alerts.value = unwrapList(alertResult.value).map((row) => {
        const alert = normalizeAlert(row); const plot = plots.value.find((item) => item.plotNo === alert.plotId); const farm = farms.value.find((item) => item.farmId === plot?.farmId)
        return { ...alert, id: alert.alertId, plotNo: alert.plotId, plotName: plot?.name || alert.plotName || alert.plotId, farmId: plot?.farmId || '', farmName: farm?.name || '', occurTime: alert.occurTime, handledAt: alert.handledAt, process: [] }
      })
      initialized.value = true
    } catch (error) { loadError.value = error.message || '平台数据加载失败'; throw error }
    finally { loading.value = false }
  }

  function log(user, module, action, result = '成功') { auditLogs.value.unshift({ id: `LOG${Date.now()}`, time: timeText(), user, module, action, result, ip: '-' }) }
  async function addDevice(data) {
    if (!isMock) {
      const response = await createDevice({ deviceNo: data.deviceNo, mqttDeviceId: data.mqttDeviceId, type: deviceTypeCode[data.type] || data.type, plotId: data.plotNo })
      devices.value.unshift({ ...normalizeDevice(response?.data || response), farmId: data.farmId || '', plotNo: data.plotNo, plotId: data.plotNo }); return
    }
    const next = String(Math.max(0, ...devices.value.map((item) => Number(String(item.id).replace(/\D/g, '')) || 0)) + 1).padStart(3, '0')
    devices.value.unshift({ id: `D${next}`, ...data, status: '在线', lastHeartbeat: '-', latestValue: '-' }); log('当前用户', '设备管理', `录入设备 ${data.deviceNo}`)
  }
  async function bindDevice(deviceId, plotNo) {
    const device = devices.value.find((item) => normalizeId(item.id) === normalizeId(deviceId)); if (!device) return
    if (!isMock) await bindDeviceApi(deviceId, plotNo)
    const old = device.plotNo || device.plotId || '未绑定'; const plot = plots.value.find((item) => item.plotNo === plotNo); device.plotNo = plotNo; device.plotId = plotNo; device.farmId = plot?.farmId || device.farmId; log('当前用户', '设备绑定', `${deviceId} ${old} → ${plotNo}`)
  }
  async function unbindDevice(deviceId) {
    const device = devices.value.find((item) => normalizeId(item.id) === normalizeId(deviceId)); if (!device) return
    if (!isMock) await unbindDeviceApi(deviceId)
    const old = device.plotNo || device.plotId; device.plotNo = ''; device.plotId = ''; log('当前用户', '设备绑定', `${deviceId} 从 ${old} 解绑`)
  }
  async function toggleUser(userId) {
    const user = users.value.find((item) => normalizeId(item.id) === normalizeId(userId)); if (!user) return
    const active = user.status !== '正常'; if (!isMock) await updateUserActive(userId, active)
    user.status = active ? '正常' : '禁用'; log('当前用户', '用户管理', `${active ? '恢复' : '禁用'}账号 ${userId}`)
  }
  async function resetPassword(userId) { if (!isMock) await resetUserPassword(userId); log('当前用户', '用户管理', `重置账号 ${userId} 密码`) }
  async function saveUser(data) {
    if (!isMock) {
      const payload = { username: data.username, name: data.name, email: data.email, phone: data.phone, active: data.status !== '禁用', role_codes: data.roles.map((item) => roleCode[item] || item), farm_ids: Array.isArray(data.farmScope) ? data.farmScope : String(data.farmScope || '').split(',').map((item) => item.trim()).filter(Boolean), plot_ids: Array.isArray(data.plotScope) ? data.plotScope : String(data.plotScope || '').split(',').map((item) => item.trim()).filter(Boolean) }
      const response = await saveUserApi(data.id, payload); const saved = normalizePlatformUser(response?.data || response)
      const index = users.value.findIndex((item) => item.id === saved.id); if (index >= 0) users.value[index] = saved; else users.value.unshift(saved); return
    }
    const current = users.value.find((item) => item.id === data.id)
    if (current) Object.assign(current, data); else users.value.unshift({ ...data, id: `U${String(users.value.length + 1).padStart(3, '0')}`, lastLogin: '-', status: '正常' })
    log('当前用户', '用户管理', `${current ? '修改' : '新增'}账号 ${data.username}`)
  }
  function saveParams(next) { Object.assign(params.value, next); log('当前用户', '系统参数', '更新运行参数') }
  async function handleAlert(alertId) {
    const alert = alerts.value.find((item) => normalizeId(item.id) === normalizeId(alertId)); if (!alert) return
    if (!isMock) await acknowledgeAlert(alertId)
    alert.status = '处理中'; alert.handledAt = timeText(); alert.process ||= []; alert.process.push(`${timeText()} 确认告警`); log('当前用户', '全局告警', `确认告警 ${alertId}`)
  }

  return { farms, plots, devices, users, alerts, auditLogs, params, loading, initialized, loadError, capabilities, onlineDevices, offlineDevices, unhandledAlerts, commandSuccessRate, loadData, addDevice, bindDevice, unbindDevice, toggleUser, resetPassword, saveUser, saveParams, handleAlert }
})
