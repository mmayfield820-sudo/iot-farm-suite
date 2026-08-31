<template>
  <div class="farmer-page dashboard">
    <div class="page-head">
      <div>
        <h1 class="page-title">农场运行总览</h1>
        <p class="page-subtitle">集中查看地块状态、设备在线情况和待处理告警</p>
      </div>
      <div class="realtime-badge"><span></span> 数据持续更新中</div>
    </div>

    <el-row :gutter="20" class="stat-row">
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover"><div class="stat-icon stat-icon-primary"><el-icon size="28"><MapLocation /></el-icon></div><div class="stat-info"><div class="stat-value">{{ plotStore.plots.length }}</div><div class="stat-label">总地块数</div></div></el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover"><div class="stat-icon stat-icon-success"><el-icon size="28"><CircleCheck /></el-icon></div><div class="stat-info"><div class="stat-value value-success">{{ plotStore.onlineCount }}</div><div class="stat-label">在线设备</div></div></el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover"><div class="stat-icon stat-icon-danger"><el-icon size="28"><Warning /></el-icon></div><div class="stat-info"><div class="stat-value value-danger">{{ plotStore.unhandledAlertCount }}</div><div class="stat-label">未处理告警</div></div></el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover"><div class="stat-icon stat-icon-primary"><el-icon size="28"><Pouring /></el-icon></div><div class="stat-info"><div class="stat-value value-primary">{{ plotStore.irrigatingCount }}</div><div class="stat-label">灌溉中</div></div></el-card>
      </el-col>
    </el-row>

    <el-card class="plot-card-container">
      <template #header>
        <div class="card-header">
          <span class="header-title"><el-icon><MapLocation /></el-icon> 地块状态监控</span>
          <el-radio-group v-model="filterStatus" size="small">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="normal">正常</el-radio-button>
            <el-radio-button label="dry">偏干</el-radio-button>
            <el-radio-button label="alert">告警</el-radio-button>
            <el-radio-button label="irrigating">灌溉中</el-radio-button>
            <el-radio-button label="offline">离线</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col v-for="plot in filteredPlots" :key="plot.plotId" :xs="24" :sm="12" :md="8" :lg="8" class="plot-col">
          <el-card class="plot-item" shadow="hover" :style="{ borderLeft: '5px solid ' + getStatusConfig(plot.status).color }" @click="goToStatus(plot)">
            <div class="plot-header">
              <div class="plot-title"><span class="plot-name">{{ plot.plotName }}</span><el-tag :type="getStatusConfig(plot.status).type" size="small" effect="dark">{{ getStatusConfig(plot.status).label }}</el-tag></div>
              <div class="plot-crop">{{ plot.cropName }}</div>
            </div>
            <el-divider />
            <div class="plot-metrics">
              <div class="metric"><span class="metric-label">环境温度</span><span class="metric-value">{{ plot.temperature }}℃</span></div>
              <div class="metric"><span class="metric-label">土壤湿度</span><span class="metric-value" :style="{ color: getHumidityColor(plot.humidity, plot.threshold) }">{{ plot.humidity }}%</span></div>
              <div class="metric"><span class="metric-label">设备状态</span><el-tag :type="plot.deviceOnline ? 'success' : 'danger'" size="small">{{ plot.deviceOnline ? '在线' : '离线' }}</el-tag></div>
            </div>
            <div class="management-summary">
              <div class="summary-head"><span>农事进度</span><strong>{{ managementOf(plot).taskCompletionRate }}%</strong></div>
              <div class="task-counts"><span>待完成 {{ managementOf(plot).pendingTaskCount }}</span><span :class="{ danger: managementOf(plot).overdueTaskCount }">逾期 {{ managementOf(plot).overdueTaskCount }}</span><span>已完成 {{ managementOf(plot).completedTaskCount }}</span></div>
              <div class="management-meta"><span :class="{ danger: managementOf(plot).pendingReminderCount }">待处理提醒 {{ managementOf(plot).pendingReminderCount }}</span><span>最近灌溉 {{ irrigationText(managementOf(plot).latestIrrigation) }}</span></div>
            </div>
            <div v-if="plot.unhandledAlerts > 0" class="plot-alert"><el-tag type="danger" size="small" effect="dark"><el-icon><Warning /></el-icon> {{ plot.unhandledAlerts }} 条未处理告警</el-tag></div>
            <div class="plot-footer"><span class="update-time"><el-icon><Clock /></el-icon> 更新于 {{ formatTimestamp(plot.updateTime) }}</span></div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-if="filteredPlots.length === 0" description="暂无符合条件的地块" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { usePlotStore } from '@/stores/plot'
import { useUserStore } from '@/stores/user'
import { usePlatformStore } from '@/stores/platform'
import { mockPlots } from '@/mock/farmAdminData'
import { getFarmManagementStatistics } from '@/api/platform'
import { formatDateTime, normalizePlot, unwrapList } from '@/utils/dataAdapters'
import { getHumidityStatus, getStatusConfig } from '@/utils/farmAdminStatus'

const router = useRouter()
const plotStore = usePlotStore()
const userStore = useUserStore()
const platformStore = usePlatformStore()
const filterStatus = ref('all')
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

onMounted(async () => {
  try {
    const scopedFarmIds = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
    if (isMock) {
      const farmIds = scopedFarmIds.length ? scopedFarmIds : [...new Set(mockPlots.map((plot) => String(plot.farmId)))]
      plotStore.setPlots(mockPlots.filter((plot) => farmIds.includes(String(plot.farmId))).map((plot) => ({ ...plot, management: emptyManagement() })))
      return
    }
    await platformStore.loadData()
    const farmIds = scopedFarmIds.length ? scopedFarmIds : platformStore.farms.map((farm) => String(farm.farmId))
    const statistics = await loadManagementStatistics(farmIds)
    const basePlots = platformStore.plots.filter((plot) => farmIds.includes(String(plot.farmId)))
    plotStore.setPlots(basePlots.map((base) => {
      const devices = platformStore.devices.filter((device) => String(device.plotId) === String(base.plotNo))
      const alerts = platformStore.alerts.filter((alert) => String(alert.plotId) === String(base.plotNo))
      const farm = platformStore.farms.find((item) => String(item.farmId) === String(base.farmId))
      const plot = normalizePlot({ ...base, plotId: base.plotNo }, { devices, alerts, farm })
      return { ...plot, management: statistics.get(String(plot.plotId)) || emptyManagement() }
    }))
  } catch (error) {
    ElMessage.error(error.message || '农场数据加载失败')
  }
})

const filteredPlots = computed(() => filterStatus.value === 'all' ? plotStore.plots : plotStore.plots.filter((plot) => plot.status === filterStatus.value))
function emptyManagement() { return { pendingReminderCount: 0, completedTaskCount: 0, pendingTaskCount: 0, overdueTaskCount: 0, taskCompletionRate: 0, latestIrrigation: null } }
async function loadManagementStatistics(farmIds) {
  const results = await Promise.allSettled(farmIds.map((farmId) => getFarmManagementStatistics(farmId)))
  return results.reduce((statistics, result) => {
    if (result.status !== 'fulfilled') return statistics
    unwrapList(result.value).forEach((item) => statistics.set(String(item.plotId), item))
    return statistics
  }, new Map())
}
function managementOf(plot) { return plot.management || emptyManagement() }
function irrigationText(irrigation) {
  if (!irrigation?.requestedAt) return '暂无'
  const action = irrigation.action === 'irrigation_on' ? '开启' : '关闭'
  return `${action} · ${formatDateTime(irrigation.executedAt || irrigation.requestedAt).slice(5, 16)}`
}
const getHumidityColor = (humidity, threshold) => ({ alert: '#F56C6C', dry: '#E6A23C', normal: '#67C23A' }[getHumidityStatus(humidity, threshold)])
const formatTimestamp = (value) => formatDateTime(value, '-')
function goToStatus(plot) {
  if (!plot.deviceOnline) ElMessage.warning(`${plot.plotName} 设备离线，请先检查设备状态`)
  router.push({ path: '/farm/status', query: { plotId: plot.plotId } })
}
</script>

<style scoped>
.dashboard { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.page-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; }
.realtime-badge { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px solid #d9ebe3; border-radius: 10px; color: #527067; background: #fff; font-size: 12px; }.realtime-badge span { width: 8px; height: 8px; border-radius: 50%; background: #35a273; box-shadow: 0 0 0 4px #e2f5eb; }
.stat-row { margin-bottom: 22px; }.stat-card, .plot-card-container, .plot-item { border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 8px 28px rgba(20, 69, 53, .05); }.stat-card { margin-bottom: 12px; }.stat-card :deep(.el-card__body) { display: flex; align-items: center; padding: 20px; }.stat-icon { width: 52px; height: 52px; flex: 0 0 52px; display: grid; place-items: center; margin-right: 15px; border-radius: 14px; }.stat-icon-primary { color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, white); }.stat-icon-success { color: #2d9466; background: #e9f7f0; }.stat-icon-danger { color: #d95858; background: #fdf0f0; }.stat-value { color: #203c33; font-size: 27px; font-weight: 750; line-height: 1.15; }.value-primary { color: var(--accent); }.value-success { color: #2d9466; }.value-danger { color: #d95858; }.stat-label { margin-top: 5px; color: #81918b; font-size: 13px; }
.plot-card-container { margin-bottom: 20px; }.plot-card-container :deep(.el-card__header) { padding: 18px 22px; border-bottom-color: #edf2ef; }.plot-card-container :deep(> .el-card__body) { padding: 22px; }.card-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; }.header-title { display: flex; align-items: center; gap: 8px; color: #27483d; font-size: 16px; font-weight: 700; }.header-title .el-icon { color: var(--accent); }.plot-col { margin-bottom: 20px; }
.plot-item { height: 100%; cursor: pointer; transition: transform .2s ease, box-shadow .2s ease; }.plot-item :deep(.el-card__body) { padding: 18px 20px; }.plot-item:hover { transform: translateY(-3px); box-shadow: 0 14px 32px rgba(20, 69, 53, .11); }.plot-title { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 5px; }.plot-name { color: #203c33; font-size: 16px; font-weight: 700; }.plot-crop { color: #84938e; font-size: 13px; }.plot-item :deep(.el-divider--horizontal) { margin: 12px 0; }.plot-metrics { display: grid; grid-template-columns: 1fr 1fr; column-gap: 22px; row-gap: 2px; }.metric { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 7px 0; }.metric-label { color: #87968f; font-size: 12px; }.metric-value { color: #28443a; font-size: 14px; font-weight: 700; }.management-summary { display: grid; gap: 8px; margin-top: 13px; padding: 11px 0; border-top: 1px solid #edf2ef; border-bottom: 1px solid #edf2ef; }.summary-head, .task-counts, .management-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; }.summary-head { color: #61786e; font-size: 12px; }.summary-head strong { color: #287457; font-size: 15px; }.task-counts { justify-content: flex-start; color: #61786e; font-size: 12px; }.task-counts span { padding-right: 9px; border-right: 1px solid #e6eeea; }.task-counts span:last-child { border-right: 0; }.management-meta { color: #7f9089; font-size: 11px; }.danger { color: #c74c4c !important; font-weight: 700; }.plot-alert { margin-top: 11px; }.plot-footer { margin-top: 12px; padding-top: 11px; border-top: 1px dashed #dfe9e5; }.update-time { display: flex; align-items: center; gap: 5px; color: #9aa7a2; font-size: 12px; }
@media (max-width: 1100px) { .card-header { align-items: flex-start; flex-direction: column; }.card-header :deep(.el-radio-group) { max-width: 100%; overflow-x: auto; } } @media (max-width: 640px) { .page-head { flex-direction: column; }.plot-card-container :deep(> .el-card__body) { padding: 16px; }.plot-metrics { grid-template-columns: 1fr; } }
</style>
