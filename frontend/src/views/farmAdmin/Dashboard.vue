<template>
  <div class="farmer-page dashboard">
    <div class="page-head">
      <div>
        <h1 class="page-title">农场运行总览</h1>
        <p class="page-subtitle">集中查看地块状态、设备在线情况和待处理告警</p>
      </div>
      <div class="realtime-badge"><span></span> 数据持续更新中</div>
    </div>
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon stat-icon-primary">
            <el-icon size="28"><MapLocation /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ plotStore.plots.length }}</div>
            <div class="stat-label">总地块数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon stat-icon-success">
            <el-icon size="28"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value value-success">{{ plotStore.onlineCount }}</div>
            <div class="stat-label">在线设备</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon stat-icon-danger">
            <el-icon size="28"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value value-danger">{{ plotStore.unhandledAlertCount }}</div>
            <div class="stat-label">未处理告警</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon stat-icon-primary">
            <el-icon size="28"><Pouring /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value value-primary">{{ plotStore.irrigatingCount }}</div>
            <div class="stat-label">灌溉中</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <FarmManagementStats :farm-ids="farmAdminStore.selectedFarmIds" />

    <!-- 状态筛选 + 地块卡片 -->
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
        <el-col 
          v-for="plot in filteredPlots" 
          :key="plot.plotId" 
          :xs="24" :sm="12" :md="8" :lg="8"
          style="margin-bottom: 20px;"
        >
          <el-card 
            class="plot-item" 
            shadow="hover"
            :style="{ borderLeft: '5px solid ' + getStatusConfig(plot.status).color }"
            @click="goToStatus(plot)"
          >
            <div class="plot-header">
              <div class="plot-title">
                <span class="plot-name">{{ plot.plotName }}</span>
                <el-tag :type="getStatusConfig(plot.status).type" size="small" effect="dark">
                  {{ getStatusConfig(plot.status).label }}
                </el-tag>
              </div>
              <div class="plot-crop">{{ plot.cropName }}</div>
            </div>

            <el-divider style="margin: 12px 0;" />

            <div class="plot-metrics">
              <div class="metric">
                <span class="metric-label">环境温度</span>
                <span class="metric-value">{{ plot.temperature }}℃</span>
              </div>
              <div class="metric">
                <span class="metric-label">土壤湿度</span>
                <span class="metric-value" :style="{ color: getHumidityColor(plot.humidity, plot.threshold) }">
                  {{ plot.humidity }}%
                </span>
              </div>
              <div class="metric">
                <span class="metric-label">湿度阈值</span>
                <span class="metric-value">{{ plot.threshold }}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">设备状态</span>
                <el-tag :type="plot.deviceOnline ? 'success' : 'danger'" size="small">
                  {{ plot.deviceOnline ? '在线' : '离线' }}
                </el-tag>
              </div>
            </div>

            <div v-if="plot.unhandledAlerts > 0" class="plot-alert">
              <el-tag type="danger" size="small" effect="dark">
                <el-icon><Warning /></el-icon> {{ plot.unhandledAlerts }} 条未处理告警
              </el-tag>
            </div>

            <div class="plot-footer">
              <span class="update-time"><el-icon><Clock /></el-icon> 更新于 {{ plot.updateTime }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-empty v-if="filteredPlots.length === 0" description="暂无符合条件的地块" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePlotStore } from '@/stores/plot'
import { useFarmAdminStore } from '@/stores/farmAdmin'
import { getStatusConfig, getHumidityStatus } from '@/utils/farmAdminStatus'
import { mockPlots } from '@/mock/farmAdminData'
import { ElMessage } from 'element-plus'
import { usePlatformStore } from '@/stores/platform'
import { normalizePlot } from '@/utils/dataAdapters'
import FarmManagementStats from '@/components/FarmManagementStats.vue'

const router = useRouter()
const plotStore = usePlotStore()
const farmAdminStore = useFarmAdminStore()
const platformStore = usePlatformStore()
const filterStatus = ref('all')
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

function syncPlots() {
  const farmIds = farmAdminStore.selectedFarmIds
  if (isMock) {
    plotStore.setPlots(mockPlots.filter((plot) => farmIds.includes(String(plot.farmId))))
    return
  }
  const basePlots = platformStore.plots.filter((plot) => farmIds.includes(String(plot.farmId)))
  plotStore.setPlots(basePlots.map((base) => {
    const devices = platformStore.devices.filter((device) => device.plotId === base.plotNo)
    const alerts = platformStore.alerts.filter((alert) => alert.plotId === base.plotNo)
    const farm = platformStore.farms.find((item) => item.farmId === base.farmId)
    return normalizePlot({ ...base, plotId: base.plotNo }, { devices, alerts, farm })
  }))
}

onMounted(async () => {
  try {
    await platformStore.loadData()
    syncPlots()
  } catch (error) {
    ElMessage.error(error.message || '农场数据加载失败')
  }
})

watch(() => farmAdminStore.selectedFarmIds.join('|'), () => {
  filterStatus.value = 'all'
  syncPlots()
})

const filteredPlots = computed(() => {
  if (filterStatus.value === 'all') return plotStore.plots
  return plotStore.plots.filter(p => p.status === filterStatus.value)
})

const getHumidityColor = (humidity, threshold) => {
  const status = getHumidityStatus(humidity, threshold)
  const colors = { alert: '#F56C6C', dry: '#E6A23C', normal: '#67C23A' }
  return colors[status]
}

const goToStatus = (plot) => {
  if (!plot.deviceOnline) {
    ElMessage.warning(`${plot.plotName} 设备离线，请先检查设备状态`)
  }
  router.push({
    path: '/farm/status',
    query: { plotId: plot.plotId }
  })
}
</script>

<style scoped>
.dashboard { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.page-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; }
.realtime-badge { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px solid #d9ebe3; border-radius: 10px; color: #527067; background: #fff; font-size: 12px; }
.realtime-badge span { width: 8px; height: 8px; border-radius: 50%; background: #35a273; box-shadow: 0 0 0 4px #e2f5eb; }
.stat-row { margin-bottom: 22px; }
.stat-card, .plot-card-container, .plot-item { border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 8px 28px rgba(20, 69, 53, .05); }
.stat-card { margin-bottom: 12px; }
.stat-card :deep(.el-card__body) { display: flex; align-items: center; padding: 20px; }
.stat-icon { width: 52px; height: 52px; flex: 0 0 52px; display: grid; place-items: center; margin-right: 15px; border-radius: 14px; }
.stat-icon-primary { color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, white); }
.stat-icon-success { color: #2d9466; background: #e9f7f0; }
.stat-icon-danger { color: #d95858; background: #fdf0f0; }
.stat-value { color: #203c33; font-size: 27px; font-weight: 750; line-height: 1.15; }
.value-primary { color: var(--accent); }.value-success { color: #2d9466; }.value-danger { color: #d95858; }
.stat-label { margin-top: 5px; color: #81918b; font-size: 13px; }
.plot-card-container { margin-bottom: 20px; }
.plot-card-container :deep(.el-card__header) { padding: 18px 22px; border-bottom-color: #edf2ef; }
.plot-card-container :deep(> .el-card__body) { padding: 22px; }
.card-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.header-title { display: flex; align-items: center; gap: 8px; color: #27483d; font-size: 16px; font-weight: 700; }
.header-title .el-icon { color: var(--accent); }
.card-header :deep(.el-radio-button__inner) { border-color: #dce8e3; color: #5e746c; box-shadow: none; }
.card-header :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) { border-color: var(--accent); background: var(--accent); box-shadow: -1px 0 0 0 var(--accent); color: white; }
.plot-item { height: 100%; cursor: pointer; transition: transform .2s ease, box-shadow .2s ease; }
.plot-item :deep(.el-card__body) { padding: 18px 20px; }
.plot-item:hover { transform: translateY(-3px); box-shadow: 0 14px 32px rgba(20, 69, 53, .11); }
.plot-title { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 5px; }
.plot-name { color: #203c33; font-size: 16px; font-weight: 700; }
.plot-crop { color: #84938e; font-size: 13px; }
.plot-metrics { display: grid; grid-template-columns: 1fr 1fr; column-gap: 22px; row-gap: 2px; }
.metric { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 7px 0; }
.metric-label { color: #87968f; font-size: 12px; }
.metric-value { color: #28443a; font-size: 14px; font-weight: 700; }
.plot-alert { margin-top: 11px; }
.plot-alert :deep(.el-tag) { border: 0; border-radius: 8px; }
.plot-footer { margin-top: 12px; padding-top: 11px; border-top: 1px dashed #dfe9e5; }
.update-time { display: flex; align-items: center; gap: 5px; color: #9aa7a2; font-size: 12px; }
@media (max-width: 1100px) { .card-header { align-items: flex-start; flex-direction: column; }.card-header :deep(.el-radio-group) { max-width: 100%; overflow-x: auto; } }
@media (max-width: 640px) { .page-head { flex-direction: column; }.realtime-badge { margin-top: -10px; }.plot-card-container :deep(> .el-card__body) { padding: 16px; }.plot-metrics { grid-template-columns: 1fr; } }
</style>
