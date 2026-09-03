import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { platformAlerts, platformAuditLogs, platformDevices, platformFarms, platformPlots, platformUsers } from '@/mock/platformData'
import { acknowledgeAlert, getAlertList } from '@/api/alert'
import { bindDevice as bindDeviceApi, createDevice, createFarm, createPlot, getAllDevices, getFarmList, getFarmOverview, getPlotList, getUserList, resetUserPassword, saveUser as saveUserApi, unbindDevice as unbindDeviceApi, updateFarm, updatePlot, updateUserActive } from '@/api/platform'
import { formatDateTime, normalizeAlert, normalizeDevice, normalizeFarm, normalizeId, normalizePlot, overviewMetricsToReport, unwrapList } from '@/utils/dataAdapters'

const clone = (value) => JSON.parse(JSON.stringify(value))
const isMock = import.meta.env.VITE_USE_MOCK === 'true'
const timeText = () => formatDateTime(new Date())
const roleLabel = { farmer: '农户', farmAdmin: '农场管理员', farm_admin: '农场管理员', systemAdmin: '系统管理员', system_admin: '系统管理员' }
const roleCode = { 农户: 'farmer', 农场管理员: 'farm_admin', 系统管理员: 'system_admin', farmer: 'farmer', farmAdmin: 'farm_admin', systemAdmin: 'system_admin' }
const deviceTypeCode = { 温度传感器: 'temperature', 湿度传感器: 'humidity', 灌溉设备: 'irrigation' }
const asArray = (value) => Array.isArray(value) ? value : typeof value === 'string' ? value.split(',').map((item) => item.trim()).filter(Boolean) : []

const normalizePlatformPlot = (row = {}) => ({
  ...row,
  internalId: normalizeId(row.internalId ?? row.plot_id ?? row.plotId ?? row.id),
  plotNo: normalizeId(row.plotNo ?? row.plot_id ?? row.plotId ?? row.id),
  farmId: normalizeId(row.farmId ?? row.farm_id),
  code: row.code || row.plotCode || row.plot_code || '',
  name: row.name || row.plotName || row.plot_name || '未命名地块',
  crop: row.crop || row.cropName || row.crop_name || '暂未种植',
  note: row.note || row.description || '',
  location: row.location || '',
  areaMu: row.areaMu ?? row.area_mu ?? null,
  irrigationMethod: row.irrigationMethod ?? row.irrigation_method ?? null,
  farmerEmployeeNo: row.farmerEmployeeNo || row.farmer_employee_no || '',
  farmerName: row.farmerName || row.farmer_name || '',
  status: row.status || row.plotStatus || row.plot_status || (row.active === false || row.Active === false ? 'inactive' : 'active'),
  active: (row.status || row.plotStatus || row.plot_status) ? (row.status || row.plotStatus || row.plot_status) === 'active' : row.active ?? row.Active ?? true,
  updatedAt: row.updatedAt || row.updated_at || '',
})
const normalizePlatformUser = (row = {}) => {
  const rawRoles = asArray(row.roles || row.roleCodes || row.role_codes || row.roleList || row.role_list)
  const roles = rawRoles.map((item) => item?.roleName || item?.role_name || roleLabel[item?.roleCode || item?.role_code || item] || item).filter(Boolean)
  const activeAssignment = (item) => item?.active !== false && item?.Active !== false && (!item?.expiresAt && !item?.expires_at || new Date(item.expiresAt || item.expires_at).getTime() > Date.now())
  const farmIds = asArray(row.farmIds || row.farm_ids || row.userFarmRoles || row.user_farm_roles).filter(activeAssignment).map((item) => normalizeId(item?.farmId ?? item?.farm_id ?? item))
  const plotIds = asArray(row.plotIds || row.plot_ids || row.userPlotRoles || row.user_plot_roles).filter(activeAssignment).map((item) => normalizeId(item?.plotId ?? item?.plot_id ?? item))
  const status = row.status || (row.active === false || row.Active === false ? 'disabled' : 'active')
  return {
    ...row,
    id: normalizeId(row.id ?? row.userId ?? row.user_id),
    employeeNo: row.employeeNo || row.employee_no || '',
    idCardMasked: row.idCardMasked || row.id_card_masked || '',
    name: row.name || row.displayName || row.display_name || row.employeeNo || row.employee_no || '',
    email: row.email || '',
    phone: row.phone || '',
    roles,
    roleCodes: asArray(row.roleCodes || row.role_codes || rawRoles.map((item) => roleCode[item] || item)),
    farmIds,
    plotIds,
    farmScope: farmIds.join(', ') || '-',
    plotScope: plotIds.join(', ') || '-',
    lastLogin: row.lastLogin || row.last_login || '-',
    status,
    statusLabel: { pending_activation: '待激活', active: '正常', disabled: '已停用' }[status] || status,
    activatedAt: row.activatedAt || row.activated_at || '',
    updatedAt: row.updatedAt || row.updated_at || '',
  }
}

export const usePlatformStore = defineStore('platform', () => {
  const farms = ref(isMock ? clone(platformFarms) : [])
  const selectedFarmId = ref(normalizeId(farms.value[0]?.farmId))
  const plots = ref(isMock ? clone(platformPlots) : [])
  const devices = ref(isMock ? clone(platformDevices) : [])
  const users = ref(isMock ? clone(platformUsers).map(normalizePlatformUser) : [])
  const alerts = ref(isMock ? clone(platformAlerts) : [])
  const auditLogs = ref(isMock ? clone(platformAuditLogs) : [])
  const loading = ref(false)
  const initialized = ref(false)
  const loadError = ref('')
  const capabilities = { auditLogs: isMock }
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
      if (!farms.value.some((farm) => farm.farmId === selectedFarmId.value)) selectedFarmId.value = farms.value[0]?.farmId || ''
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
  function selectFarm(farmId) { selectedFarmId.value = normalizeId(farmId) }
  async function saveFarm(data) {
    const payload = {
      name: data.name.trim(),
      province: data.province.trim(),
      city: data.city.trim(),
      address: data.address.trim() || null,
      areaMu: data.areaMu === '' || data.areaMu === null ? null : Number(data.areaMu),
      managerEmployeeNo: data.managerEmployeeNo?.trim() || null,
      note: data.note.trim() || null,
    }
    if (!isMock) {
      const response = data.farmId ? await updateFarm(data.farmId, { ...payload, status: data.status }) : await createFarm(payload)
      const saved = normalizeFarm(response?.data || response)
      const index = farms.value.findIndex((item) => item.farmId === saved.farmId)
      if (index >= 0) farms.value[index] = saved
      else farms.value.unshift(saved)
      return saved
    }
    const manager = users.value.find((item) => item.employeeNo === payload.managerEmployeeNo)
    if (payload.managerEmployeeNo && !manager) throw new Error('MANAGER_EMPLOYEE_NOT_FOUND')
    const mockPayload = { ...payload, managerName: manager?.name || null }
    const current = farms.value.find((item) => item.farmId === data.farmId)
    if (current) {
      Object.assign(current, mockPayload, { status: data.status, active: data.status === 'active', updatedAt: timeText() })
      log('当前用户', '基础档案', `修改橙园 ${current.farmId}`)
      return current
    }
    const next = Math.max(0, ...farms.value.map((item) => Number(String(item.farmId).replace(/\D/g, '')) || 0)) + 1
    const saved = normalizeFarm({ id: `F${String(next).padStart(3, '0')}`, ...mockPayload, status: 'active', createdAt: timeText(), updatedAt: timeText() })
    farms.value.unshift(saved)
    log('当前用户', '基础档案', `新增橙园 ${saved.farmId}`)
    return saved
  }
  async function toggleFarm(farmId) {
    const farm = farms.value.find((item) => item.farmId === farmId)
    if (!farm) return
    return saveFarm({ ...farm, status: farm.status === 'active' ? 'inactive' : 'active' })
  }
  async function listFarmPlots({ farmId, page = 1, pageSize = 10, keyword = '', status = '' }) {
    if (!isMock) {
      const response = await getPlotList({ farmId, page, pageSize, keyword: keyword || undefined, status: status || undefined })
      const items = unwrapList(response).map(normalizePlatformPlot)
      return { items, total: Number(response?.total ?? response?.data?.total ?? items.length) }
    }
    const query = keyword.trim().toLowerCase()
    const matched = plots.value.filter((item) => !farmId || item.farmId === farmId)
      .filter((item) => !status || item.status === status)
      .filter((item) => !query || `${item.code} ${item.name} ${item.location}`.toLowerCase().includes(query))
    const offset = (page - 1) * pageSize
    return { items: matched.slice(offset, offset + pageSize), total: matched.length }
  }
  async function savePlot(data) {
    const payload = {
      farmId: data.farmId,
      code: data.code.trim(),
      name: data.name.trim(),
      areaMu: data.areaMu === '' || data.areaMu === null ? null : Number(data.areaMu),
      location: data.location.trim() || null,
      status: data.status || 'active',
    }
    if (!isMock) {
      const response = data.plotId ? await updatePlot(data.plotId, payload) : await createPlot(payload)
      const saved = normalizePlatformPlot(response?.data || response)
      const index = plots.value.findIndex((item) => item.plotNo === saved.plotNo)
      if (index >= 0) plots.value[index] = { ...plots.value[index], ...saved }
      else plots.value.unshift(saved)
      return saved
    }
    const current = plots.value.find((item) => item.plotNo === data.plotId)
    if (current) {
      Object.assign(current, payload, { updatedAt: timeText(), active: payload.status === 'active' })
      log('当前用户', '基础档案', `修改地块 ${current.plotNo}`)
      return current
    }
    const next = Math.max(0, ...plots.value.map((item) => Number(String(item.plotNo).replace(/\D/g, '')) || 0)) + 1
    const saved = normalizePlatformPlot({ id: `P${String(next).padStart(3, '0')}`, ...payload, createdAt: timeText(), updatedAt: timeText() })
    plots.value.unshift(saved)
    log('当前用户', '基础档案', `新增地块 ${saved.plotNo}`)
    return saved
  }
  async function togglePlot(plot) {
    return savePlot({ ...plot, plotId: plot.plotNo, status: plot.status === 'active' ? 'inactive' : 'active' })
  }
  async function addDevice(data) {
    if (!isMock) {
      const response = await createDevice({ deviceNo: data.deviceNo, deviceUuid: data.deviceUuid, type: deviceTypeCode[data.type] || data.type, plotId: data.plotNo })
      devices.value.unshift(normalizeDevice(response?.data || response)); return
    }
    const next = String(Math.max(0, ...devices.value.map((item) => Number(String(item.id).replace(/\D/g, '')) || 0)) + 1).padStart(3, '0')
    devices.value.unshift({ id: `D${next}`, ...data, status: '在线', lastHeartbeat: '-', latestValue: '-' }); log('当前用户', '设备管理', `录入设备 ${data.deviceNo}`)
  }
  async function bindDevice(deviceId, plotNo) {
    const device = devices.value.find((item) => normalizeId(item.id) === normalizeId(deviceId)); if (!device) return
    if (!isMock) await bindDeviceApi(deviceId, plotNo)
    const old = device.plotNo || device.plotId || '未绑定'; device.plotNo = plotNo; device.plotId = plotNo; log('当前用户', '设备绑定', `${deviceId} ${old} → ${plotNo}`)
  }
  async function unbindDevice(deviceId) {
    const device = devices.value.find((item) => normalizeId(item.id) === normalizeId(deviceId)); if (!device) return
    if (!isMock) await unbindDeviceApi(deviceId)
    const old = device.plotNo || device.plotId; device.plotNo = ''; device.plotId = ''; log('当前用户', '设备绑定', `${deviceId} 从 ${old} 解绑`)
  }
  async function listUsers({ page = 1, pageSize = 10, keyword = '', role = '', status = '' } = {}) {
    if (!isMock) {
      const response = await getUserList({ page, pageSize, keyword: keyword || undefined, role: role || undefined, status: status || undefined })
      const items = unwrapList(response).map(normalizePlatformUser)
      users.value = items
      return { items, total: Number(response?.total ?? response?.data?.total ?? items.length) }
    }
    const query = keyword.trim().toLowerCase()
    const matched = users.value.filter((item) => !query || `${item.employeeNo} ${item.name} ${item.phone}`.toLowerCase().includes(query))
      .filter((item) => !role || item.roleCodes?.includes(role))
      .filter((item) => !status || item.status === status)
    const offset = (page - 1) * pageSize
    return { items: matched.slice(offset, offset + pageSize), total: matched.length }
  }
  async function toggleUser(userId) {
    const user = users.value.find((item) => normalizeId(item.id) === normalizeId(userId)); if (!user) return
    const active = user.status === 'disabled'
    if (!isMock) {
      const response = await updateUserActive(userId, active)
      Object.assign(user, normalizePlatformUser(response?.data || response))
    } else Object.assign(user, { status: active ? 'active' : 'disabled', statusLabel: active ? '正常' : '已停用' })
    log('当前用户', '用户管理', `${active ? '启用' : '停用'}账号 ${userId}`)
    return user
  }
  async function resetPassword(userId) {
    const response = !isMock ? await resetUserPassword(userId) : null
    const target = users.value.find((item) => normalizeId(item.id) === normalizeId(userId))
    if (target) Object.assign(target, { status: 'pending_activation', statusLabel: '待激活', activatedAt: '' })
    log('当前用户', '用户管理', `重置账号 ${userId} 密码`)
    return response?.data || response
  }
  async function saveUser(data) {
    const roleCodes = data.roleCodes || data.roles.map((item) => roleCode[item] || item)
    const farmIds = data.farmIds || asArray(data.farmScope)
    const plotIds = data.plotIds || asArray(data.plotScope)
    if (!isMock) {
      const payload = { name: data.name.trim(), email: data.email?.trim() || null, phone: data.phone?.trim() || null, roleCodes, farmIds, plotIds }
      if (!data.id) Object.assign(payload, { employeeNo: data.employeeNo.trim(), idCardNo: data.idCardNo.trim() })
      else if (data.idCardNo?.trim()) payload.idCardNo = data.idCardNo.trim()
      const response = await saveUserApi(data.id, payload); const raw = response?.data || response; const saved = normalizePlatformUser(raw)
      const index = users.value.findIndex((item) => item.id === saved.id); if (index >= 0) users.value[index] = saved; else users.value.unshift(saved)
      return saved
    }
    const current = users.value.find((item) => item.id === data.id)
    const saved = normalizePlatformUser({ ...data, employeeNo: data.employeeNo, roleCodes, farmIds, plotIds, id: data.id || `U${String(users.value.length + 1).padStart(3, '0')}`, status: current?.status || 'pending_activation' })
    if (current) Object.assign(current, saved); else users.value.unshift(saved)
    log('当前用户', '用户管理', `${current ? '修改' : '新增'}账号 ${saved.employeeNo}`)
    return saved
  }
  async function handleAlert(alertId) {
    const alert = alerts.value.find((item) => normalizeId(item.id) === normalizeId(alertId)); if (!alert) return
    if (!isMock) await acknowledgeAlert(alertId)
    alert.status = '处理中'; alert.handledAt = timeText(); alert.process ||= []; alert.process.push(`${timeText()} 确认告警`); log('当前用户', '全局告警', `确认告警 ${alertId}`)
  }

  return { farms, selectedFarmId, plots, devices, users, alerts, auditLogs, loading, initialized, loadError, capabilities, onlineDevices, offlineDevices, unhandledAlerts, commandSuccessRate, loadData, selectFarm, saveFarm, toggleFarm, listFarmPlots, savePlot, togglePlot, addDevice, bindDevice, unbindDevice, listUsers, toggleUser, resetPassword, saveUser, handleAlert }
})
