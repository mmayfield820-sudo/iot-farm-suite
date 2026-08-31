<template>
  <div class="farmer-page device-monitor-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">地块设备监测</h1>
        <p class="page-subtitle">按地块查看传感器读数、设备连接状态和灌溉设备当前运行状态。</p>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="7" :lg="6">
        <el-card class="plot-list-card">
          <template #header><div class="list-header"><span><el-icon><MapLocation /></el-icon> 地块</span><el-tag size="small" type="info">{{ plotStore.plots.length }} 块</el-tag></div></template>
          <el-menu :default-active="selectedPlotId" class="plot-menu" @select="handlePlotSelect">
            <el-menu-item v-for="plot in plotStore.plots" :key="plot.plotId" :index="plot.plotId" :class="{ 'is-offline': !plot.deviceOnline }">
              <div class="menu-item-content">
                <div class="menu-plot-info"><span class="menu-plot-name">{{ plot.plotName }}</span><small>{{ plot.deviceOnline ? '设备在线' : '设备离线' }}<template v-if="plot.unhandledAlerts"> · {{ plot.unhandledAlerts }} 条告警</template></small></div>
                <span class="menu-humidity" :style="{ color: getHumidityColor(plot.humidity, plot.threshold) }">{{ plot.humidity }}%</span>
              </div>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="17" :lg="18">
        <template v-if="currentPlot">
          <section class="monitor-summary">
            <div><h2>{{ currentPlot.plotName }}</h2><p>{{ currentPlot.cropName }} · 数据更新于 {{ formatTimestamp(currentPlot.updateTime) }}</p></div>
            <div class="summary-tags"><el-tag :type="currentPlot.deviceOnline ? 'success' : 'danger'" effect="dark">{{ currentPlot.deviceOnline ? '设备在线' : '设备离线' }}</el-tag><el-tag v-if="currentPlot.unhandledAlerts" type="danger">{{ currentPlot.unhandledAlerts }} 条待处理告警</el-tag></div>
          </section>

          <el-row :gutter="16" class="monitor-grid">
            <el-col :xs="24" :sm="8">
              <el-card class="monitor-card">
                <span class="monitor-label">土壤湿度</span>
                <strong class="monitor-value" :style="{ color: getHumidityColor(currentPlot.humidity, currentPlot.threshold) }">{{ currentPlot.humidity }}<small>%</small></strong>
                <p>参考阈值 {{ currentPlot.threshold }}%</p>
                <div class="device-line"><span>{{ getDeviceState('humidity').label }}</span><el-tag :type="getDeviceState('humidity').online ? 'success' : 'danger'" size="small">{{ getDeviceState('humidity').online ? '在线' : '离线' }}</el-tag></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-card class="monitor-card">
                <span class="monitor-label">环境温度</span>
                <strong class="monitor-value temperature">{{ currentPlot.temperature }}<small>℃</small></strong>
                <p>当前采集读数</p>
                <div class="device-line"><span>{{ getDeviceState('temperature').label }}</span><el-tag :type="getDeviceState('temperature').online ? 'success' : 'danger'" size="small">{{ getDeviceState('temperature').online ? '在线' : '离线' }}</el-tag></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-card class="monitor-card">
                <span class="monitor-label">灌溉设备</span>
                <strong class="monitor-value irrigation">{{ currentPlot.irrigating ? '灌溉中' : '待命' }}</strong>
                <p>{{ currentPlot.irrigating ? '当前地块正在执行灌溉' : '当前没有进行中的灌溉' }}</p>
                <div class="device-line"><span>{{ getDeviceState('irrigation').label }}</span><el-tag :type="getDeviceState('irrigation').online ? 'success' : 'danger'" size="small">{{ getDeviceState('irrigation').online ? '在线' : '离线' }}</el-tag></div>
              </el-card>
            </el-col>
          </el-row>
        </template>
        <el-empty v-else description="暂无可监测的地块" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { usePlotStore } from '@/stores/plot'
import { useUserStore } from '@/stores/user'
import { usePlatformStore } from '@/stores/platform'
import { mockPlots } from '@/mock/farmAdminData'
import { formatDateTime, normalizePlot } from '@/utils/dataAdapters'
import { getHumidityStatus } from '@/utils/farmAdminStatus'

const route = useRoute()
const router = useRouter()
const plotStore = usePlotStore()
const userStore = useUserStore()
const platformStore = usePlatformStore()
const selectedPlotId = ref('')
const isMock = import.meta.env.VITE_USE_MOCK === 'true'
const currentPlot = computed(() => plotStore.getPlotById(selectedPlotId.value))

function getDeviceState(type) {
  const device = currentPlot.value?.devices?.[type]
  const labels = { humidity: '湿度传感器', temperature: '温度传感器', irrigation: '灌溉设备' }
  return { online: Boolean(device?.online ?? currentPlot.value?.deviceOnline), label: device?.deviceNo || device?.deviceId || labels[type] }
}
function formatTimestamp(value) { return formatDateTime(value, '-') }
function getHumidityColor(humidity, threshold) {
  return ({ alert: '#d95858', dry: '#d18a32', normal: '#2d9466' })[getHumidityStatus(humidity, threshold)]
}
function handlePlotSelect(plotId) {
  selectedPlotId.value = plotId
  router.replace({ query: { plotId } })
}

onMounted(async () => {
  const scopedFarmIds = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
  let scopedPlots = []
  try {
    if (isMock) {
      const farmIds = scopedFarmIds.length ? scopedFarmIds : [...new Set(mockPlots.map((plot) => String(plot.farmId)))]
      scopedPlots = mockPlots.filter((plot) => farmIds.includes(String(plot.farmId)))
    } else {
      await platformStore.loadData()
      const farmIds = scopedFarmIds.length ? scopedFarmIds : platformStore.farms.map((farm) => String(farm.farmId))
      const basePlots = platformStore.plots.filter((plot) => farmIds.includes(String(plot.farmId)))
      scopedPlots = basePlots.map((base) => {
        const devices = platformStore.devices.filter((device) => String(device.plotId) === String(base.plotNo))
        const alerts = platformStore.alerts.filter((alert) => String(alert.plotId) === String(base.plotNo))
        const farm = platformStore.farms.find((item) => String(item.farmId) === String(base.farmId))
        return normalizePlot({ ...base, plotId: base.plotNo }, { devices, alerts, farm })
      })
    }
  } catch (error) {
    ElMessage.error(error.message || '设备监测数据加载失败')
  }
  plotStore.setPlots(scopedPlots)
  const plotId = Array.isArray(route.query.plotId) ? route.query.plotId[0] : route.query.plotId
  selectedPlotId.value = plotStore.plots.find((plot) => String(plot.plotId) === String(plotId))?.plotId || plotStore.plots[0]?.plotId || ''
})
</script>

<style scoped>
.device-monitor-page{animation:fadeIn .25s ease}@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}.plot-list-card,.monitor-card{border:1px solid var(--line);border-radius:8px;box-shadow:0 5px 18px rgba(20,69,53,.04)}.plot-list-card{margin-bottom:18px;overflow:hidden}.plot-list-card :deep(.el-card__header){padding:16px 18px;border-bottom-color:#edf2ef}.plot-list-card :deep(.el-card__body){padding:7px}.list-header{display:flex;align-items:center;justify-content:space-between;color:#29483c;font-size:14px;font-weight:700}.list-header span{display:flex;align-items:center;gap:7px}.list-header .el-icon{color:var(--accent)}.plot-menu{border:0}.plot-menu :deep(.el-menu-item){height:auto;min-height:62px;margin:3px 0;padding:10px 12px!important;border-radius:7px;line-height:1.4}.plot-menu :deep(.el-menu-item:hover){background:#f3f8f5}.plot-menu :deep(.el-menu-item.is-active){color:var(--accent);background:#edf7f1;font-weight:650}.menu-item-content{display:flex;align-items:center;justify-content:space-between;width:100%;gap:10px}.menu-plot-info{min-width:0}.menu-plot-name,.menu-plot-info small{display:block}.menu-plot-name{color:#345347;font-size:13px}.menu-plot-info small{margin-top:4px;color:#8a9993;font-size:11px}.menu-humidity{font-size:17px;font-weight:750}.is-offline .menu-plot-name{color:#8d9d96}.monitor-summary{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:16px;padding:17px 20px;border:1px solid #dceae3;border-radius:8px;background:#fbfdfc}.monitor-summary h2{margin:0;color:#29483c;font-size:19px}.monitor-summary p{margin:6px 0 0;color:#84948d;font-size:12px}.summary-tags{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:7px}.summary-tags .el-tag{border-radius:6px}.monitor-grid{margin-bottom:18px}.monitor-card{height:100%;min-height:196px}.monitor-card :deep(.el-card__body){display:flex;flex-direction:column;height:100%;padding:20px}.monitor-label{color:#71847b;font-size:12px}.monitor-value{margin-top:10px;color:#29483c;font-size:32px;line-height:1.1}.monitor-value small{margin-left:3px;font-size:14px}.monitor-value.temperature{color:#cb7b2c}.monitor-value.irrigation{color:var(--accent);font-size:26px}.monitor-card p{min-height:18px;margin:8px 0 16px;color:#8b9993;font-size:12px}.device-line{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:auto;padding-top:13px;border-top:1px solid #edf2ef;color:#61786e;font-size:12px}.device-line .el-tag{border-radius:6px}@media(max-width:900px){.plot-list-card{margin-bottom:16px}}@media(max-width:620px){.monitor-summary{align-items:stretch;flex-direction:column}.summary-tags{justify-content:flex-start}}
</style>
