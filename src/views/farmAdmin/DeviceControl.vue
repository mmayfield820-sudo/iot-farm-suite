<template>
  <div class="farmer-page control-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">灌溉设备控制</h1>
        <p class="page-subtitle">选择目标地块，核对实时数据后下发控制指令</p>
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

      <!-- 右侧控制面板 -->
      <el-col :xs="24" :sm="24" :md="17" :lg="18">
        <div v-if="currentPlot" class="control-panel">
          <el-card class="panel-header">
            <div class="header-content">
              <div class="plot-info">
                <h2 class="plot-title">{{ currentPlot.plotName }}</h2>
                <span class="plot-crop">{{ currentPlot.cropName }}</span>
              </div>
              <div class="device-status">
                <el-tag 
                  :type="currentPlot.deviceOnline ? 'success' : 'danger'" 
                  size="large" effect="dark" class="status-tag"
                >
                  <el-icon v-if="currentPlot.deviceOnline"><CircleCheck /></el-icon>
                  <el-icon v-else><CircleClose /></el-icon>
                  {{ currentPlot.deviceOnline ? '设备在线' : '设备离线' }}
                </el-tag>
                <div class="device-id">设备: {{ currentPlot.deviceId }}</div>
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
              </el-card>
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-card class="metric-card">
                <div class="metric-label">环境温度</div>
                <div class="metric-value-large" style="color: #E6A23C;">
                  {{ currentPlot.temperature }}<span class="unit">℃</span>
                </div>
                <div class="metric-desc">适宜作物生长</div>
              </el-card>
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-card class="metric-card">
                <div class="metric-label">灌溉时长上限</div>
                <div class="metric-value-large irrigation-limit">
                  {{ currentPlot.maxDuration }}<span class="unit">分钟</span>
                </div>
                <div class="metric-desc">超过将自动提醒</div>
              </el-card>
            </el-col>
          </el-row>

          <el-card class="control-area">
            <template #header>
              <div class="control-header">
                <span><el-icon><Operation /></el-icon> 灌溉控制</span>
                <el-tag v-if="currentPlot.irrigating" type="primary" effect="dark" size="large">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  灌溉进行中...
                </el-tag>
              </div>
            </template>

            <el-alert
              v-if="!currentPlot.deviceOnline"
              title="设备离线，禁止远程控制"
              type="error"
              description="该设备已超过规定时间未上报心跳，无法执行远程控制。请检查设备电源和网络连接。"
              :closable="false" show-icon class="offline-alert"
            />

            <div class="control-buttons" v-else>
              <div class="button-group">
                <el-button
                  type="primary" size="large" class="control-btn open-btn"
                  :disabled="currentPlot.irrigating || controlLoading"
                  @click="handleOpen"
                >
                  <el-icon size="24"><SwitchButton /></el-icon>
                  <div class="btn-text">
                    <div class="btn-title">开启灌溉</div>
                    <div class="btn-desc">向设备发送开启指令</div>
                  </div>
                </el-button>
                <el-button
                  type="danger" size="large" class="control-btn close-btn"
                  :disabled="!currentPlot.irrigating || controlLoading"
                  @click="handleClose"
                >
                  <el-icon size="24"><CircleClose /></el-icon>
                  <div class="btn-text">
                    <div class="btn-title">关闭灌溉</div>
                    <div class="btn-desc">向设备发送关闭指令</div>
                  </div>
                </el-button>
              </div>

              <div v-if="controlState.visible" class="control-state">
                <el-alert
                  :title="controlState.title"
                  :type="controlState.type"
                  :description="controlState.description"
                  show-icon :closable="false" class="state-alert"
                >
                  <template #default>
                    <div v-if="controlState.loading" class="state-loading">
                      <el-progress :percentage="controlState.progress" :stroke-width="6" />
                      <span class="loading-text">{{ controlState.loadingText }}</span>
                    </div>
                  </template>
                </el-alert>
              </div>
            </div>
          </el-card>

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

    <el-dialog v-model="confirmDialog.visible" :title="confirmDialog.title" width="420px" center destroy-on-close>
      <div class="confirm-content">
        <div class="confirm-icon">{{ confirmDialog.icon }}</div>
        <div class="confirm-message">{{ confirmDialog.message }}</div>
        <el-descriptions :column="1" border size="small" class="confirm-detail">
          <el-descriptions-item label="目标地块">{{ confirmDialog.plotName }}</el-descriptions-item>
          <el-descriptions-item label="当前湿度">{{ confirmDialog.humidity }}%</el-descriptions-item>
          <el-descriptions-item label="湿度阈值">{{ confirmDialog.threshold }}%</el-descriptions-item>
          <el-descriptions-item label="设备状态">
            <el-tag :type="confirmDialog.deviceOnline ? 'success' : 'danger'" size="small">
              {{ confirmDialog.deviceOnline ? '在线' : '离线' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="confirmDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="executeControl" :loading="controlLoading">确认执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlotStore } from '@/stores/plot'
import { useUserStore } from '@/stores/user'
import { getHumidityStatus, IRRIGATION_STATUS } from '@/utils/farmAdminStatus'
import { mockPlots, mockIrrigationRecords } from '@/mock/farmAdminData'
import { ElMessage } from 'element-plus'
import { usePlatformStore } from '@/stores/platform'
import { getPlotDetail } from '@/api/plot'
import { controlIrrigation, getIrrigationRecords } from '@/api/device'
import { normalizeIrrigationRecord, normalizePlot, unwrapList } from '@/utils/dataAdapters'

const route = useRoute()
const router = useRouter()
const plotStore = usePlotStore()
const userStore = useUserStore()
const platformStore = usePlatformStore()
const selectedPlotId = ref('')
const controlLoading = ref(false)
const records = ref([])
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

const controlState = ref({ visible: false, title: '', type: 'info', description: '', loading: false, progress: 0, loadingText: '' })
const confirmDialog = ref({ visible: false, title: '', icon: '', message: '', plotName: '', humidity: 0, threshold: 0, deviceOnline: true, action: '' })

const currentPlot = computed(() => plotStore.getPlotById(selectedPlotId.value))
const currentRecords = computed(() => records.value.filter(r => r.plotId === selectedPlotId.value))

onMounted(async () => {
  const farmIds = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
  let scopedPlots = []
  if (isMock) {
    scopedPlots = mockPlots.filter((plot) => farmIds.includes(String(plot.farmId)))
  } else {
    try {
      await platformStore.loadData()
      const basePlots = platformStore.plots.filter((plot) => farmIds.includes(String(plot.farmId)))
      const details = await Promise.allSettled(basePlots.map((plot) => getPlotDetail(plot.plotNo)))
      scopedPlots = basePlots.map((base, index) => {
        const detail = details[index].status === 'fulfilled' ? (details[index].value?.data || details[index].value) : {}
        const devices = platformStore.devices.filter((device) => device.plotId === base.plotNo)
        const alerts = platformStore.alerts.filter((alert) => alert.plotId === base.plotNo)
        const farm = platformStore.farms.find((item) => item.farmId === base.farmId)
        return normalizePlot({ ...base, ...detail, plotId: base.plotNo }, { devices, alerts, farm })
      })
      const recordResults = await Promise.allSettled(scopedPlots.map((plot) => getIrrigationRecords(plot.plotId)))
      records.value = recordResults.flatMap((result) => result.status === 'fulfilled' ? unwrapList(result.value).map(normalizeIrrigationRecord) : [])
    } catch (error) {
      ElMessage.error(error.message || '灌溉数据加载失败')
    }
  }
  const scopedPlotIds = scopedPlots.map((plot) => String(plot.plotId))
  plotStore.setPlots(scopedPlots)
  if (isMock) records.value = mockIrrigationRecords.filter((record) => scopedPlotIds.includes(String(record.plotId)))
  const plotId = Array.isArray(route.query.plotId) ? route.query.plotId[0] : route.query.plotId
  if (plotId && plotStore.plots.find(p => p.plotId === plotId)) {
    selectedPlotId.value = plotId
  } else if (plotStore.plots.length > 0) {
    selectedPlotId.value = plotStore.plots[0].plotId
  }
})

const handlePlotSelect = (plotId) => {
  selectedPlotId.value = plotId
  controlState.value.visible = false
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

const handleOpen = () => {
  const plot = currentPlot.value
  confirmDialog.value = { visible: true, title: '确认开启灌溉', icon: '🚿', message: '您即将对该地块开启灌溉，请确认以下信息：', plotName: plot.plotName, humidity: plot.humidity, threshold: plot.threshold, deviceOnline: plot.deviceOnline, action: 'open' }
}
const handleClose = () => {
  const plot = currentPlot.value
  confirmDialog.value = { visible: true, title: '确认关闭灌溉', icon: '⏹️', message: '您即将关闭该设备的灌溉，请确认：', plotName: plot.plotName, humidity: plot.humidity, threshold: plot.threshold, deviceOnline: plot.deviceOnline, action: 'close' }
}

const executeControl = async () => {
  controlLoading.value = true
  confirmDialog.value.visible = false
  const plot = currentPlot.value
  const action = confirmDialog.value.action
  controlState.value = { visible: true, title: '指令下发中', type: 'info', description: `正在向 ${plot.plotName} 的 ${plot.deviceId} 发送${action === 'open' ? '开启' : '关闭'}指令...`, loading: true, progress: 30, loadingText: '正在连接设备...' }
  await simulateProgress()
  let isSuccess = true
  let response = null
  try {
    if (!isMock) response = await controlIrrigation({ plot_id: plot.plotId, device_id: plot.devices?.irrigation?.deviceId || null, action_type: action === 'open' ? '开启' : '关闭', activation_type: '手动' })
    isSuccess = isMock ? Math.random() > 0.1 : !['失败', '超时'].includes(response?.status || response?.data?.status)
  } catch {
    isSuccess = false
  }
  if (isSuccess) {
    if (action === 'open') {
      plotStore.updatePlot(plot.plotId, { irrigating: true, status: 'irrigating' })
      records.value.unshift({ recordId: 'IR' + Date.now(), plotId: plot.plotId, deviceId: plot.deviceId, operator: userStore.user.displayName, operatorId: userStore.user.id, operationType: '开启', activationType: '手动', startTime: formatDateTime(new Date()), endTime: '', duration: '-', status: '进行中', source: '手动' })
      controlState.value = { visible: true, title: '执行成功', type: 'success', description: `${plot.plotName} 的灌溉设备已成功开启，设备正在运行中。`, loading: false, progress: 100, loadingText: '' }
      ElMessage.success('灌溉开启成功')
    } else {
      plotStore.updatePlot(plot.plotId, { irrigating: false, status: getHumidityStatus(plot.humidity, plot.threshold) })
      const activeRecord = records.value.find(r => r.plotId === plot.plotId && r.status === '进行中')
      if (activeRecord) {
        const endTime = new Date()
        const start = new Date(activeRecord.startTime)
        activeRecord.endTime = formatDateTime(endTime)
        activeRecord.duration = Math.round((endTime - start) / 60000)
        activeRecord.status = '成功'
      }
      controlState.value = { visible: true, title: '执行成功', type: 'success', description: `${plot.plotName} 的灌溉设备已成功关闭。`, loading: false, progress: 100, loadingText: '' }
      ElMessage.success('灌溉关闭成功')
    }
  } else {
    if (action === 'open') {
      records.value.unshift({ recordId: 'IR' + Date.now(), plotId: plot.plotId, deviceId: plot.deviceId, operator: userStore.user.displayName, operatorId: userStore.user.id, operationType: '开启', startTime: formatDateTime(new Date()), endTime: formatDateTime(new Date()), duration: 0, status: '失败', source: '页面' })
    }
    controlState.value = { visible: true, title: '执行失败', type: 'error', description: '设备响应超时或网络异常，指令未能成功下发。请检查设备状态后重试。', loading: false, progress: 100, loadingText: '' }
    ElMessage.error('指令执行失败')
  }
  controlLoading.value = false
}

const simulateProgress = () => {
  return new Promise((resolve) => {
    let progress = 30
    const timer = setInterval(() => {
      progress += Math.random() * 20
      if (progress >= 90) { progress = 90; clearInterval(timer); setTimeout(resolve, 500) }
      controlState.value.progress = Math.min(progress, 90)
      if (progress > 50) controlState.value.loadingText = '等待设备响应...'
      if (progress > 70) controlState.value.loadingText = '接收设备确认...'
    }, 400)
  })
}
const refreshRecords = async () => {
  if (isMock) return ElMessage.success('记录已刷新')
  try {
    const results = await Promise.allSettled(plotStore.plots.map((plot) => getIrrigationRecords(plot.plotId)))
    records.value = results.flatMap((result) => result.status === 'fulfilled' ? unwrapList(result.value).map(normalizeIrrigationRecord) : [])
    ElMessage.success('记录已刷新')
  } catch (error) { ElMessage.error(error.message || '记录刷新失败') }
}
const formatDateTime = (date) => {
  const pad = (n) => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}
</script>

<style scoped>
.control-page { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.page-head { display: flex; justify-content: space-between; }
.plot-list-card, .panel-header, .metric-card, .control-area, .records-card { border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 8px 28px rgba(20, 69, 53, .05); }
.plot-list-card { margin-bottom: 20px; overflow: hidden; }
.plot-list-card :deep(.el-card__header), .control-area :deep(.el-card__header), .records-card :deep(.el-card__header) { padding: 17px 20px; border-bottom-color: #edf2ef; }
.plot-list-card :deep(.el-card__body) { padding: 8px; }
.list-header, .control-header, .records-header { display: flex; justify-content: space-between; align-items: center; color: #28483d; font-size: 15px; font-weight: 700; }
.list-header > span, .control-header > span, .records-header > span { display: flex; align-items: center; gap: 8px; }
.list-header .el-icon, .control-header .el-icon, .records-header .el-icon { color: var(--accent); }
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
.device-status { text-align: right; }
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
.humidity-progress { margin: 13px 0 7px; }
.control-area { margin-bottom: 20px; }
.control-area :deep(.el-card__body) { padding: 22px; }
.offline-alert { margin: 2px 0; border-radius: 11px; }
.control-buttons { padding: 8px 0 2px; }
.button-group { display: flex; justify-content: center; gap: 18px; margin-bottom: 18px; }
.control-btn { width: 210px; height: 78px; display: flex; flex-direction: row; align-items: center; justify-content: center; gap: 12px; border-radius: 13px; }
.open-btn { border-color: var(--accent); background: var(--accent); }
.open-btn:hover { border-color: color-mix(in srgb, var(--accent) 84%, black); background: color-mix(in srgb, var(--accent) 84%, black); }
.control-btn :deep(.el-icon) { margin: 0 !important; }
.btn-text { text-align: left; }
.btn-title { font-size: 15px; font-weight: 700; }
.btn-desc { margin-top: 3px; font-size: 11px; opacity: .82; }
.control-state { margin-top: 18px; }
.state-alert { border-radius: 11px; }
.state-alert :deep(.el-alert__content) { width: 100%; }
.state-loading { margin-top: 10px; }
.loading-text { display: block; margin-top: 6px; color: #81918b; font-size: 12px; }
.records-card { margin-bottom: 20px; overflow: hidden; }
.records-card :deep(.el-card__body) { padding: 0 20px 20px; }
.records-card :deep(.el-table) { --el-table-header-bg-color: #f3f8f5; --el-table-row-hover-bg-color: #f5faf7; border-radius: 10px; }
.confirm-content { padding: 8px 0; text-align: center; }
.confirm-icon { width: 66px; height: 66px; display: grid; place-items: center; margin: 0 auto 14px; border-radius: 20px; background: #eef7f2; font-size: 34px; }
.confirm-message { margin-bottom: 20px; color: #345046; font-size: 15px; font-weight: 600; }
.confirm-detail { margin-top: 15px; text-align: left; }
@media (max-width: 900px) { .button-group { gap: 12px; }.control-btn { width: 48%; }.plot-list-card { margin-bottom: 20px; } }
@media (max-width: 560px) { .header-content { align-items: flex-start; flex-direction: column; }.device-status { text-align: left; }.button-group { flex-direction: column; }.control-btn { width: 100%; }.records-card :deep(.el-card__body) { padding: 0 12px 14px; } }
</style>
