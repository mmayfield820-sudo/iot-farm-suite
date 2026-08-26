<template>
  <div class="farmer-page device-status-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">设备状态</h1>
        <p class="page-subtitle">选择目标地块，查看温度、湿度与灌溉设备的实时运行状态</p>
      </div>
    </div>
    <el-row :gutter="20">
      <!-- 左侧地块列表 -->
      <el-col :xs="24" :sm="24" :md="7" :lg="6">
        <el-card class="plot-list-card">
          <template #header>
            <div class="list-header">
              <span><el-icon><MapLocation /></el-icon> 地块列表</span>
              <el-tag size="small" type="info">{{ plotStore.plots.length }} 块</el-tag>
            </div>
          </template>
          <el-menu
            :default-active="selectedPlotId"
            @select="handlePlotSelect"
            class="plot-menu"
          >
            <el-menu-item 
              v-for="plot in plotStore.plots" 
              :key="plot.plotId" 
              :index="plot.plotId"
              :class="{ 'is-offline': !plot.deviceOnline, 'is-irrigating': plot.irrigating }"
            >
              <div class="menu-item-content">
                <div class="menu-plot-info">
                  <span class="menu-plot-name">{{ plot.plotName }}</span>
                  <div class="menu-plot-tags">
                    <el-tag v-if="plot.irrigating" type="primary" size="small" effect="dark">灌溉中</el-tag>
                    <el-tag v-if="!plot.deviceOnline" type="danger" size="small">离线</el-tag>
                    <el-tag v-if="plot.unhandledAlerts > 0" type="danger" size="small">
                      {{ plot.unhandledAlerts }}告警
                    </el-tag>
                  </div>
                </div>
                <div class="menu-humidity" :style="{ color: getHumidityColor(plot.humidity, plot.threshold) }">
                  {{ plot.humidity }}%
                </div>
              </div>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 右侧设备状态面板 -->
      <el-col :xs="24" :sm="24" :md="17" :lg="18">
        <div v-if="currentPlot" class="status-panel">
          <el-card class="panel-header">
            <div class="header-content">
              <div class="plot-info">
                <h2 class="plot-title">{{ currentPlot.plotName }}</h2>
                <span class="plot-crop">{{ currentPlot.cropName }}</span>
              </div>
              <div class="device-status-summary">
                <el-tag 
                  :type="onlineDeviceCount === deviceCount ? 'success' : onlineDeviceCount > 0 ? 'warning' : 'danger'"
                  size="large" effect="dark" class="status-tag"
                >
                  <el-icon v-if="onlineDeviceCount === deviceCount"><CircleCheck /></el-icon>
                  <el-icon v-else><Warning /></el-icon>
                  {{ onlineDeviceCount }}/{{ deviceCount }} 台设备在线
                </el-tag>
                <div class="device-id">温度、湿度与灌溉设备</div>
              </div>
            </div>
          </el-card>

          <el-row :gutter="20" class="metrics-row">
            <el-col :xs="24" :sm="8">
              <el-card class="metric-card humidity-card">
                <div class="metric-label">当前土壤湿度</div>
                <div class="metric-value-large" :style="{ color: getHumidityColor(currentPlot.humidity, currentPlot.threshold) }">
                  {{ currentPlot.humidity }}<span class="unit">%</span>
                </div>
                <el-progress 
                  :percentage="currentPlot.humidity" 
                  :color="getProgressColor(currentPlot.humidity, currentPlot.threshold)"
                  :stroke-width="10" class="humidity-progress"
                />
                <div class="metric-threshold">阈值: {{ currentPlot.threshold }}%</div>
                <div class="metric-device-state">
                  <el-tag :type="getDeviceState('humidity').online ? 'success' : 'danger'" size="small">
                    <el-icon v-if="getDeviceState('humidity').online"><CircleCheck /></el-icon>
                    <el-icon v-else><CircleClose /></el-icon>
                    湿度设备{{ getDeviceState('humidity').online ? '在线' : '离线' }}
                  </el-tag>
                  <span>{{ getDeviceState('humidity').id }}</span>
                </div>
              </el-card>
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-card class="metric-card">
                <div class="metric-label">环境温度</div>
                <div class="metric-value-large" style="color: #E6A23C;">
                  {{ currentPlot.temperature }}<span class="unit">℃</span>
                </div>
                <div class="metric-desc">适宜作物生长</div>
                <div class="metric-device-state">
                  <el-tag :type="getDeviceState('temperature').online ? 'success' : 'danger'" size="small">
                    <el-icon v-if="getDeviceState('temperature').online"><CircleCheck /></el-icon>
                    <el-icon v-else><CircleClose /></el-icon>
                    温度设备{{ getDeviceState('temperature').online ? '在线' : '离线' }}
                  </el-tag>
                  <span>{{ getDeviceState('temperature').id }}</span>
                </div>
              </el-card>
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-card class="metric-card">
                <div class="metric-label">灌溉时长上限</div>
                <div class="metric-value-large irrigation-limit">
                  {{ currentPlot.maxDuration }}<span class="unit">分钟</span>
                </div>
                <div class="metric-desc">超过将自动提醒</div>
                <div class="metric-device-state">
                  <el-tag :type="getDeviceState('irrigation').online ? 'success' : 'danger'" size="small">
                    <el-icon v-if="getDeviceState('irrigation').online"><CircleCheck /></el-icon>
                    <el-icon v-else><CircleClose /></el-icon>
                    灌溉设备{{ getDeviceState('irrigation').online ? '在线' : '离线' }}
                  </el-tag>
                  <span>{{ getDeviceState('irrigation').id }}</span>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-card class="records-card">
            <template #header>
              <div class="records-header">
                <span><el-icon><Document /></el-icon> 近期灌溉记录</span>
                <el-button type="primary" link @click="refreshRecords">
                  <el-icon><Refresh /></el-icon> 刷新
                </el-button>
              </div>
            </template>
            <el-table :data="currentRecords" border stripe>
              <el-table-column prop="startTime" label="开始时间" width="160" />
              <el-table-column prop="endTime" label="结束时间" width="160">
                <template #default="scope">
                  <span v-if="scope.row.endTime">{{ scope.row.endTime }}</span>
                  <el-tag v-else type="primary" size="small" effect="dark">进行中</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="duration" label="时长" width="100">
                <template #default="scope">
                  <span v-if="scope.row.duration !== '-'">{{ scope.row.duration }} 分钟</span>
                  <span v-else style="color: #C0C4CC;">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="operator" label="操作人" width="120" />
              <el-table-column prop="source" label="来源" width="120">
                <template #default="scope">
                  <el-tag size="small" :type="scope.row.source === '页面' ? 'primary' : 'success'">
                    {{ scope.row.source }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="执行状态" width="120">
                <template #default="scope">
                  <el-tag :type="IRRIGATION_STATUS[scope.row.status]?.type || 'info'" size="small">
                    <el-icon v-if="scope.row.status === '进行中'" class="is-loading"><Loading /></el-icon>
                    {{ scope.row.status }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="currentRecords.length === 0" description="暂无灌溉记录" />
          </el-card>
        </div>
      </el-col>
    </el-row>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlotStore } from '@/stores/plot'
import { useFarmAdminStore } from '@/stores/farmAdmin'
import { getHumidityStatus, IRRIGATION_STATUS } from '@/utils/farmAdminStatus'
import { mockPlots, mockIrrigationRecords } from '@/mock/farmAdminData'
import { ElMessage } from 'element-plus'
import { usePlatformStore } from '@/stores/platform'
import { getIrrigationRecords } from '@/api/device'
import { normalizeIrrigationRecord, normalizePlot, unwrapList } from '@/utils/dataAdapters'

const route = useRoute()
const router = useRouter()
const plotStore = usePlotStore()
const farmAdminStore = useFarmAdminStore()
const platformStore = usePlatformStore()
const selectedPlotId = ref('')
const records = ref([])
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

const currentPlot = computed(() => plotStore.getPlotById(selectedPlotId.value))
const currentRecords = computed(() => records.value.filter(r => r.plotId === selectedPlotId.value))
const deviceCount = computed(() => ['temperature', 'humidity', 'irrigation'].length)
const onlineDeviceCount = computed(() => ['temperature', 'humidity', 'irrigation'].filter((type) => getDeviceState(type).online).length)

const getDeviceState = (type) => {
  const device = currentPlot.value?.devices?.[type]
  return {
    online: Boolean(device?.online ?? currentPlot.value?.deviceOnline),
    id: device?.deviceNo || device?.deviceId || '未绑定设备',
  }
}

async function loadSelectedFarm() {
  let scopedPlots = []
  const farmIds = farmAdminStore.selectedFarmIds
  if (isMock) {
    scopedPlots = mockPlots.filter((plot) => farmIds.includes(String(plot.farmId)))
    const scopedPlotIds = scopedPlots.map((plot) => String(plot.plotId))
    records.value = mockIrrigationRecords.filter((record) => scopedPlotIds.includes(String(record.plotId)))
  } else {
    await platformStore.loadData()
    const basePlots = platformStore.plots.filter((plot) => farmIds.includes(String(plot.farmId)))
    scopedPlots = basePlots.map((base) => {
      const devices = platformStore.devices.filter((device) => device.plotId === base.plotNo)
      const alerts = platformStore.alerts.filter((alert) => alert.plotId === base.plotNo)
      const farm = platformStore.farms.find((item) => item.farmId === base.farmId)
      return normalizePlot({ ...base, plotId: base.plotNo }, { devices, alerts, farm })
    })
    const recordResults = await Promise.allSettled(scopedPlots.map((plot) => getIrrigationRecords(plot.plotId)))
    records.value = recordResults.flatMap((result) => result.status === 'fulfilled' ? unwrapList(result.value).map(normalizeIrrigationRecord) : [])
  }
  plotStore.setPlots(scopedPlots)
  const plotId = Array.isArray(route.query.plotId) ? route.query.plotId[0] : route.query.plotId
  if (plotId && plotStore.plots.find(p => p.plotId === plotId)) {
    selectedPlotId.value = plotId
  } else if (plotStore.plots.length > 0) {
    selectedPlotId.value = plotStore.plots[0].plotId
    router.replace({ query: { ...route.query, plotId: selectedPlotId.value } })
  } else {
    selectedPlotId.value = ''
  }
}

let pageReady = false
onMounted(async () => {
  try {
    await loadSelectedFarm()
    pageReady = true
  } catch (error) {
    ElMessage.error(error.message || '灌溉数据加载失败')
  }
})

watch(() => farmAdminStore.selectedFarmIds.join('|'), async () => {
  if (!pageReady) return
  try { await loadSelectedFarm() }
  catch (error) { ElMessage.error(error.message || '农场切换失败') }
})

const handlePlotSelect = (plotId) => {
  selectedPlotId.value = plotId
  router.replace({ query: { plotId } })
}

const getHumidityColor = (humidity, threshold) => {
  const status = getHumidityStatus(humidity, threshold)
  const colors = { alert: '#F56C6C', dry: '#E6A23C', normal: '#67C23A' }
  return colors[status]
}
const getProgressColor = (humidity, threshold) => {
  if (humidity < threshold * 0.8) return '#F56C6C'
  if (humidity < threshold) return '#E6A23C'
  return '#67C23A'
}

const refreshRecords = async () => {
  if (isMock) return ElMessage.success('记录已刷新')
  try {
    const results = await Promise.allSettled(plotStore.plots.map((plot) => getIrrigationRecords(plot.plotId)))
    records.value = results.flatMap((result) => result.status === 'fulfilled' ? unwrapList(result.value).map(normalizeIrrigationRecord) : [])
    ElMessage.success('记录已刷新')
  } catch (error) { ElMessage.error(error.message || '记录刷新失败') }
}
</script>

<style scoped>
.device-status-page { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.page-head { display: flex; justify-content: space-between; }
.plot-list-card, .panel-header, .metric-card, .records-card { border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 8px 28px rgba(20, 69, 53, .05); }
.plot-list-card { margin-bottom: 20px; overflow: hidden; }
.plot-list-card :deep(.el-card__header), .records-card :deep(.el-card__header) { padding: 17px 20px; border-bottom-color: #edf2ef; }
.plot-list-card :deep(.el-card__body) { padding: 8px; }
.list-header, .records-header { display: flex; justify-content: space-between; align-items: center; color: #28483d; font-size: 15px; font-weight: 700; }
.list-header > span, .records-header > span { display: flex; align-items: center; gap: 8px; }
.list-header .el-icon, .records-header .el-icon { color: var(--accent); }
.plot-menu { border: none; }
.plot-menu :deep(.el-menu-item) { height: auto; min-height: 66px; margin: 4px 0; padding: 11px 13px !important; border-radius: 10px; color: #516860; line-height: 1.4; }
.plot-menu :deep(.el-menu-item:hover) { background: #f3f8f5; }
.plot-menu :deep(.el-menu-item.is-active) { color: var(--accent); background: color-mix(in srgb, var(--accent) 9%, white); font-weight: 700; }
.menu-item-content { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.menu-plot-info { min-width: 0; flex: 1; }
.menu-plot-name { display: block; margin-bottom: 5px; font-size: 14px; font-weight: 650; }
.menu-plot-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.menu-humidity { margin-left: 10px; font-size: 18px; font-weight: 750; }
.is-offline .menu-plot-name { color: #909f99; }
.panel-header { margin-bottom: 20px; background: linear-gradient(135deg, #fff, #f5faf7); }
.panel-header :deep(.el-card__body) { padding: 21px 24px; }
.header-content { display: flex; justify-content: space-between; align-items: center; gap: 18px; }
.plot-title { margin: 0; color: #203c33; font-size: 22px; }
.plot-crop { display: inline-block; margin-top: 5px; color: #82928c; font-size: 13px; }
.device-status-summary { text-align: right; }
.status-tag { border: 0; border-radius: 9px; font-size: 13px; }
.device-id { margin-top: 7px; color: #8b9994; font-size: 12px; }
.metrics-row { margin-bottom: 20px; }
.metric-card { height: calc(100% - 12px); margin-bottom: 12px; text-align: center; }
.metric-card :deep(.el-card__body) { padding: 22px 20px; }
.metric-label { margin-bottom: 8px; color: #83928d; font-size: 13px; }
.metric-value-large { color: #29473d; font-size: 42px; font-weight: 750; line-height: 1.25; }
.irrigation-limit { color: var(--accent); }
.unit { margin-left: 4px; font-size: 14px; font-weight: 600; }
.metric-desc, .metric-threshold { margin-top: 9px; color: #93a19c; font-size: 12px; }
.metric-device-state { display: flex; min-height: 28px; align-items: center; justify-content: center; gap: 8px; margin-top: 15px; padding-top: 13px; border-top: 1px solid #edf2ef; }
.metric-device-state .el-tag { display: inline-flex; align-items: center; gap: 3px; border-radius: 8px; }
.metric-device-state > span { color: #92a19b; font-size: 11px; }
.humidity-progress { margin: 13px 0 7px; }
.records-card { margin-bottom: 20px; overflow: hidden; }
.records-card :deep(.el-card__body) { padding: 0 20px 20px; }
.records-card :deep(.el-table) { --el-table-header-bg-color: #f3f8f5; --el-table-row-hover-bg-color: #f5faf7; border-radius: 10px; }
@media (max-width: 900px) { .plot-list-card { margin-bottom: 20px; } }
@media (max-width: 560px) { .header-content { align-items: flex-start; flex-direction: column; }.device-status-summary { text-align: left; }.records-card :deep(.el-card__body) { padding: 0 12px 14px; } }
</style>
