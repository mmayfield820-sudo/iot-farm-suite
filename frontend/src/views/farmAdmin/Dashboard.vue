<template>
  <div class="farmer-page dashboard">
    <section class="overview-head">
      <div>
        <h1>{{ greeting }}，{{ userStore.user?.displayName || '管理员' }}<span class="greeting-weather" title="晴朗"><el-icon><Sunny /></el-icon></span></h1>
        <p>掌握橙园整体运行状态，及时处理异常</p>
      </div>
      <div class="update-status">
        <span>数据更新时间： {{ dataUpdatedAt }}</span>
        <button type="button" title="刷新数据" :disabled="refreshing" @click="loadDashboard"><el-icon :class="{ rotating: refreshing }"><RefreshRight /></el-icon></button>
      </div>
    </section>

    <el-row :gutter="18" class="stat-row">
      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <article class="stat-card">
          <span class="stat-icon"><span class="plot-grid-icon" aria-hidden="true"><span></span><span></span><span></span><span></span></span></span>
          <div class="stat-content"><span class="stat-label">管理地块</span><strong class="stat-value">{{ plotStore.plots.length }} <em>个</em></strong><p>正常 {{ normalPlotCount }} <i></i> 异常 {{ abnormalPlotCount }}</p></div>
        </article>
      </el-col>
      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <article class="stat-card stage-card">
          <span class="stat-icon"><span class="stage-calendar-icon" aria-hidden="true"><span class="calendar-pins"></span><span class="calendar-clock"></span></span></span>
          <div class="stat-content"><span class="stat-label">当前计划阶段</span><div class="stage-value"><strong class="stage-main"><span>{{ currentStageCode }}</span><span class="stage-name">{{ currentStageName }}</span></strong><span>{{ currentStageStatus }}</span></div></div>
          <p class="stage-period">{{ currentStagePeriod }}</p>
        </article>
      </el-col>
      <el-col :xs="24" :sm="12" :md="12" :lg="5">
        <article class="stat-card task-stat-card">
          <span class="stat-icon"><span class="task-completion-icon" aria-hidden="true"><span class="clipboard-clip"></span><span class="clipboard-check"></span></span></span>
          <div class="stat-content"><span class="stat-label">任务完成率</span><strong class="stat-value">{{ taskCompletionRate }}%</strong><p>已完成 {{ taskCompletedCount }} / 总数 {{ taskTotalCount }}</p><p class="trend">较昨日 <strong>↑ {{ taskDailyIncrease }}%</strong></p></div>
        </article>
      </el-col>
      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <article class="stat-card alert-stat-card">
          <span class="stat-icon"><svg class="alert-warning-icon" viewBox="0 0 40 38" aria-hidden="true"><path d="M20 5 36 33H4Z"/><path d="M20 14v9"/><circle cx="20" cy="28" r="1.8"/></svg></span>
          <div class="stat-content"><span class="stat-label">告警总数</span><strong class="stat-value">{{ actionableAlerts.length }} <em>条</em></strong><p class="alert-breakdown"><span>设备异常 {{ deviceAlertCount }}</span><i></i><span>环境异常 {{ environmentAlertCount }}</span></p><p class="alert-trend">较昨日 <strong>↑ {{ alertDailyIncrease }} 条</strong></p></div>
        </article>
      </el-col>
    </el-row>

    <div class="dashboard-main-grid">
    <section class="plot-status-card">
      <header class="plot-status-head">
        <h2><el-icon><Place /></el-icon>各地块状态</h2>
        <div class="plot-status-tools">
          <el-input v-model="plotSearch" clearable placeholder="搜索地块名称或负责人" @input="currentPage = 1"><template #suffix><el-icon><Search /></el-icon></template></el-input>
          <el-popover placement="bottom-end" trigger="click" :width="180">
            <template #reference><el-button plain><el-icon><Setting /></el-icon>自定义列</el-button></template>
            <el-checkbox-group v-model="visibleColumns" class="column-options">
              <el-checkbox label="manager">负责人</el-checkbox><el-checkbox label="humidity">土壤湿度</el-checkbox><el-checkbox label="target">目标区间</el-checkbox><el-checkbox label="temperature">环境温度</el-checkbox><el-checkbox label="irrigation">灌溉建议</el-checkbox><el-checkbox label="device">设备状态</el-checkbox><el-checkbox label="tasks">待完成任务</el-checkbox>
            </el-checkbox-group>
          </el-popover>
        </div>
      </header>

      <el-table :data="pagedPlots" class="plot-status-table" empty-text="暂无符合条件的地块">
        <el-table-column prop="plotName" label="地块名称" min-width="130"><template #default="{ row }"><strong class="table-plot-name">{{ row.plotName }}</strong></template></el-table-column>
        <el-table-column v-if="columnVisible('manager')" label="负责人" min-width="105"><template #default="{ row }">{{ plotManager(row) }}</template></el-table-column>
        <el-table-column v-if="columnVisible('humidity')" label="土壤湿度(%)" min-width="125" align="center"><template #default="{ row }"><strong :class="['humidity-value', humidityTone(row)]">{{ row.humidity }}%</strong></template></el-table-column>
        <el-table-column v-if="columnVisible('target')" label="目标区间(%)" min-width="140" align="center"><template #default="{ row }">{{ targetRange(row) }}</template></el-table-column>
        <el-table-column v-if="columnVisible('temperature')" label="环境温度(℃)" min-width="130" align="center"><template #default="{ row }">{{ row.temperature }}℃</template></el-table-column>
        <el-table-column v-if="columnVisible('irrigation')" label="灌溉建议" min-width="115" align="center"><template #default="{ row }"><span :class="['irrigation-advice', irrigationAdvice(row).tone]">{{ irrigationAdvice(row).label }}</span></template></el-table-column>
        <el-table-column v-if="columnVisible('device')" label="设备状态" min-width="110" align="center"><template #default="{ row }"><span :class="['device-state', { offline: !row.deviceOnline }]"><i></i>{{ row.deviceOnline ? '正常' : '离线' }}</span></template></el-table-column>
        <el-table-column v-if="columnVisible('tasks')" label="待完成任务" min-width="105" align="center"><template #default="{ row }"><strong :class="['pending-count', { danger: managementOf(row).overdueTaskCount }]">{{ pendingTasks(row) }}</strong></template></el-table-column>
        <el-table-column label="操作" width="82" align="right"><template #default="{ row }"><el-button link type="primary" @click="goToStatus(row)">查看</el-button></template></el-table-column>
      </el-table>

      <footer class="plot-table-footer">
        <span>共 {{ filteredTablePlots.length }} 条</span>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="filteredTablePlots.length" layout="prev, pager, next" background />
        <el-select v-model="pageSize" @change="currentPage = 1"><el-option :value="5" label="5 条/页"/><el-option :value="10" label="10 条/页"/><el-option :value="20" label="20 条/页"/></el-select>
      </footer>
    </section>

    <aside class="latest-alerts-card">
      <header class="latest-alerts-head">
        <h2>最新告警</h2>
        <button type="button" @click="goToAlerts()">查看全部（{{ actionableAlerts.length }}）<el-icon><ArrowRight /></el-icon></button>
      </header>
      <div v-if="latestAlerts.length" class="latest-alert-list">
        <button v-for="alert in latestAlerts" :key="alert.alertId || alert.id" type="button" :class="['latest-alert-item', alertTone(alert)]" @click="goToAlerts(alert)">
          <span class="latest-alert-dot" aria-hidden="true"></span>
          <span class="latest-alert-icon" aria-hidden="true">
            <el-icon v-if="alertIconKind(alert) === 'moisture'"><Pouring /></el-icon>
            <el-icon v-else-if="alertIconKind(alert) === 'task'"><Calendar /></el-icon>
            <el-icon v-else-if="alertIconKind(alert) === 'device'"><SwitchButton /></el-icon>
            <el-icon v-else><Warning /></el-icon>
          </span>
          <span class="latest-alert-copy"><strong>{{ latestAlertTitle(alert) }}</strong><span>{{ alert.reason || '请查看告警详情并及时处理' }}</span></span>
          <time>{{ alertTimeLabel(alert.occurTime) }}</time>
        </button>
      </div>
      <el-empty v-else description="暂无待处理告警" :image-size="72" />
    </aside>
    </div>

    <div class="dashboard-secondary-grid">
      <section class="task-execution-card">
        <header class="task-execution-head">
          <div><h2>近期任务执行概况</h2><span>（当前阶段 {{ taskStageLabel }}）</span></div>
          <button type="button" @click="goToTasks">查看全部任务<el-icon><ArrowRight /></el-icon></button>
        </header>
        <div class="task-execution-metrics">
          <article class="task-execution-item pending">
            <svg viewBox="0 0 48 48" aria-hidden="true"><rect x="10" y="10" width="28" height="32" rx="3"/><path d="M18 10V6h12v4M17 25l4 4 9-10M17 35h14"/></svg>
            <div><span>待完成任务</span><strong>{{ taskPendingCount }} <em>项</em></strong></div>
          </article>
          <article class="task-execution-item completed">
            <svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="18"/><path d="M15 24l6 6 12-13"/></svg>
            <div><span>已完成任务</span><strong>{{ taskCompletedCount }} <em>项</em></strong></div>
          </article>
          <article class="task-execution-item overdue">
            <svg viewBox="0 0 48 48" aria-hidden="true"><rect x="7" y="10" width="34" height="32" rx="3"/><path d="M7 19h34M16 6v8M32 6v8M15 27h2M23 27h2M31 27h2M15 34h2M23 34h2M31 34h2"/></svg>
            <div><span>逾期任务</span><strong>{{ taskOverdueCount }} <em>项</em></strong></div>
          </article>
        </div>
      </section>
      <section class="key-milestones-card">
        <header class="key-milestones-head">
          <h2>近期关键节点</h2>
          <button type="button" @click="goToRecords">查看生产档案<el-icon><ArrowRight /></el-icon></button>
        </header>
        <div v-if="keyMilestones.length" class="key-milestones-list">
          <article v-for="node in keyMilestones" :key="node.type" :class="['key-milestone-item', node.tone]">
            <span class="milestone-marker" aria-hidden="true"></span>
            <div class="milestone-copy"><strong>{{ node.label }} <em>（{{ node.completed ? '已完成' : '预计' }}）</em></strong><span>{{ node.completed ? '完成时间' : '预计时间' }}：{{ node.dateRange }}</span></div>
            <div class="milestone-distance"><span>{{ node.distanceLabel }}</span><strong>{{ node.distanceValue }}</strong></div>
          </article>
        </div>
        <el-empty v-else description="暂无关键节点" :image-size="54" />
      </section>
    </div>
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
import { getFarmAnnualProduction } from '@/api/production'
import { formatDateTime, normalizePlot, parseDate, unwrapList } from '@/utils/dataAdapters'

const router = useRouter()
const plotStore = usePlotStore()
const userStore = useUserStore()
const platformStore = usePlatformStore()
const plotSearch = ref('')
const currentPage = ref(1)
const pageSize = ref(5)
const visibleColumns = ref(['manager', 'humidity', 'target', 'temperature', 'irrigation', 'device', 'tasks'])
const productionContexts = ref([])
const refreshing = ref(false)
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

onMounted(loadDashboard)

async function loadDashboard() {
  refreshing.value = true
  try {
    const scopedFarmIds = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
    if (isMock) {
      const farmIds = scopedFarmIds.length ? scopedFarmIds : [...new Set(mockPlots.map((plot) => String(plot.farmId)))]
      plotStore.setPlots(mockPlots.filter((plot) => farmIds.includes(String(plot.farmId))).map((plot) => ({ ...plot, management: emptyManagement() })))
      return
    }
    await platformStore.loadData(true)
    const farmIds = scopedFarmIds.length ? scopedFarmIds : platformStore.farms.map((farm) => String(farm.farmId))
    const [statistics, contexts] = await Promise.all([loadManagementStatistics(farmIds), loadProductionContexts(farmIds)])
    productionContexts.value = contexts
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
  } finally {
    refreshing.value = false
  }
}

const greeting = computed(() => {
  const hour = new Date().getHours()
  return hour < 11 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
})
const abnormalPlotCount = computed(() => plotStore.plots.filter((plot) => plot.status === 'alert' || plot.status === 'offline' || !plot.deviceOnline || plot.unhandledAlerts > 0).length)
const normalPlotCount = computed(() => Math.max(0, plotStore.plots.length - abnormalPlotCount.value))
const taskCompletedCount = computed(() => plotStore.plots.reduce((sum, plot) => sum + Number(managementOf(plot).completedTaskCount || 0), 0))
const taskTotalCount = computed(() => plotStore.plots.reduce((sum, plot) => sum + Number(managementOf(plot).taskTotal || 0), 0))
const taskPendingCount = computed(() => plotStore.plots.reduce((sum, plot) => sum + Number(managementOf(plot).pendingTaskCount || 0), 0))
const taskOverdueCount = computed(() => plotStore.plots.reduce((sum, plot) => sum + Number(managementOf(plot).overdueTaskCount || 0), 0))
const taskCompletionRate = computed(() => taskTotalCount.value ? Math.round(taskCompletedCount.value * 100 / taskTotalCount.value) : 0)
const taskYesterdayCompletedCount = computed(() => plotStore.plots.reduce((sum, plot) => sum + Number(managementOf(plot).yesterdayCompletedTaskCount || 0), 0))
const taskDailyIncrease = computed(() => {
  const yesterdayRate = taskTotalCount.value ? taskYesterdayCompletedCount.value * 100 / taskTotalCount.value : 0
  return Math.max(0, Math.round((taskCompletionRate.value - yesterdayRate) * 10) / 10)
})
const scopedPlotIds = computed(() => new Set(plotStore.plots.map((plot) => String(plot.plotId))))
const scopedAlerts = computed(() => platformStore.alerts.filter((alert) => scopedPlotIds.value.has(String(alert.plotId || alert.plotNo))))
const actionableAlerts = computed(() => scopedAlerts.value.filter((alert) => ['未处理', '处理中'].includes(alert.status)))
const latestAlerts = computed(() => [...actionableAlerts.value].sort((a, b) => (parseDate(b.occurTime)?.getTime() || 0) - (parseDate(a.occurTime)?.getTime() || 0)).slice(0, 5))
const deviceAlertCount = computed(() => actionableAlerts.value.filter((alert) => /设备|离线|故障|灌溉失败/.test(`${alert.typeCode || ''} ${alert.type || ''}`)).length)
const environmentAlertCount = computed(() => Math.max(0, actionableAlerts.value.length - deviceAlertCount.value))
const alertDailyIncrease = computed(() => {
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  const todayKey = formatDateTime(today, '').slice(0, 10)
  const yesterdayKey = formatDateTime(yesterday, '').slice(0, 10)
  const countFor = (key) => scopedAlerts.value.filter((alert) => String(alert.occurTime || '').slice(0, 10) === key).length
  return Math.max(0, countFor(todayKey) - countFor(yesterdayKey))
})
const sharedStage = computed(() => {
  const stages = productionContexts.value.map((context) => context?.stage).filter(Boolean)
  if (!stages.length) return null
  const first = stages[0]
  return stages.every((stage) => stage.code === first.code && stage.name === first.name) ? first : { code: '', name: '多阶段', status: 'active' }
})
const currentStageCode = computed(() => sharedStage.value?.code || (sharedStage.value ? '' : '未配置'))
const currentStageName = computed(() => sharedStage.value?.name || '')
const taskStageLabel = computed(() => sharedStage.value ? `${currentStageCode.value} ${currentStageName.value}`.trim() : '未配置')
const keyMilestones = computed(() => [
  buildMilestone('harvest', '采收完成', 'green'),
  buildMilestone('cleanup', '清园完成', 'orange'),
].filter(Boolean))
const currentStageStatus = computed(() => sharedStage.value?.status === 'active' ? '进行中' : sharedStage.value ? '待开始' : '待配置')
const currentStagePeriod = computed(() => {
  const stage = sharedStage.value
  if (!stage?.startsOn || !stage?.endsOn) return stage ? '各橙园处于不同计划阶段' : '请先配置年度生产计划'
  const end = parseDate(stage.endsOn)
  const remaining = end ? Math.max(0, Math.ceil((end.getTime() - Date.now()) / 86400000)) : null
  const range = `${stage.startsOn.slice(5)} ~ ${stage.endsOn.slice(5)}`
  return remaining === null ? `计划周期： ${range}` : `计划周期： ${range}（剩余 ${remaining} 天）`
})
const dataUpdatedAt = computed(() => {
  const latest = plotStore.plots.map((plot) => parseDate(plot.updateTime)).filter(Boolean).sort((a, b) => b - a)[0]
  return formatDateTime(latest || new Date(), '-').slice(0, 16)
})
const filteredTablePlots = computed(() => {
  const keyword = plotSearch.value.trim().toLowerCase()
  if (!keyword) return plotStore.plots
  return plotStore.plots.filter((plot) => `${plot.plotName} ${plotManager(plot)}`.toLowerCase().includes(keyword))
})
const pagedPlots = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTablePlots.value.slice(start, start + pageSize.value)
})

function emptyManagement() { return { pendingReminderCount: 0, taskTotal: 0, completedTaskCount: 0, yesterdayCompletedTaskCount: 0, pendingTaskCount: 0, yesterdayPendingTaskCount: 0, overdueTaskCount: 0, yesterdayOverdueTaskCount: 0, taskCompletionRate: 0, latestIrrigation: null } }
async function loadManagementStatistics(farmIds) {
  const results = await Promise.allSettled(farmIds.map((farmId) => getFarmManagementStatistics(farmId)))
  return results.reduce((statistics, result) => {
    if (result.status !== 'fulfilled') return statistics
    unwrapList(result.value).forEach((item) => statistics.set(String(item.plotId), item))
    return statistics
  }, new Map())
}
async function loadProductionContexts(farmIds) {
  const results = await Promise.allSettled(farmIds.map((farmId) => getFarmAnnualProduction(farmId)))
  return results.filter((result) => result.status === 'fulfilled').map((result) => result.value)
}
function managementOf(plot) { return plot.management || emptyManagement() }
function columnVisible(key) { return visibleColumns.value.includes(key) }
function plotManager(plot) {
  const directName = plot.farmerName || plot.managerName || plot.responsibleName
  if (directName) return directName
  const assigned = platformStore.users.find((user) => String(user.plotScope || '').split(',').map((item) => item.trim()).includes(String(plot.plotId)))
  return assigned?.name || '未分配'
}
function targetBounds(plot) {
  const context = productionContexts.value.find((item) => String(item.farmId) === String(plot.farmId))
  const stage = context?.stage || sharedStage.value
  const fallbackMin = Number(plot.threshold || 0)
  const min = stage?.moistureMin != null && Number.isFinite(Number(stage.moistureMin)) ? Number(stage.moistureMin) : fallbackMin
  const max = stage?.moistureMax != null && Number.isFinite(Number(stage.moistureMax)) ? Number(stage.moistureMax) : Math.min(100, min + 15)
  return { min, max }
}
function targetRange(plot) {
  const { min, max } = targetBounds(plot)
  return `${min}% ~ ${max}%`
}
function humidityTone(plot) {
  const { min, max } = targetBounds(plot)
  if (plot.humidity < min * .8 || plot.humidity > max * 1.15) return 'danger'
  if (plot.humidity < min || plot.humidity > max) return 'warning'
  return 'success'
}
function irrigationAdvice(plot) {
  if (!plot.deviceOnline) return { label: '检查设备', tone: 'danger' }
  if (plot.humidity < targetBounds(plot).min) return { label: '建议灌溉', tone: 'warning' }
  return { label: '暂不灌溉', tone: 'success' }
}
function pendingTasks(plot) { return Number(managementOf(plot).pendingTaskCount || 0) + Number(managementOf(plot).overdueTaskCount || 0) }
function buildMilestone(type, label, tone) {
  const contexts = productionContexts.value.filter(Boolean)
  if (!contexts.length) return null
  const completionKey = type === 'harvest' ? 'harvestCompletedAt' : 'cleanupCompletedAt'
  const completedDates = contexts.map((context) => parseDate(context[completionKey])).filter(Boolean)
  const allCompleted = completedDates.length === contexts.length
  if (allCompleted) {
    const completedAt = completedDates.sort((a, b) => b - a)[0]
    return { type, label, tone, completed: true, dateRange: formatDateTime(completedAt, '').slice(0, 10), distanceLabel: '完成状态', distanceValue: '已记录' }
  }
  const dates = []
  contexts.forEach((context) => {
    const tasks = (context.planItems || []).filter((task) => task.taskType === type)
    tasks.forEach((task) => {
      const scheduled = parseDate(task.scheduledDate)
      if (scheduled) dates.push(scheduled)
      const stage = (context.stages || []).find((item) => item.code === task.stageCode)
      const stageEnd = parseDate(stage?.endsOn)
      if (stageEnd) dates.push(stageEnd)
    })
    if (!tasks.length && type === 'harvest') {
      const stage = (context.stages || []).find((item) => /采收/.test(item.name || ''))
      const startsOn = parseDate(stage?.startsOn)
      const endsOn = parseDate(stage?.endsOn)
      if (startsOn) dates.push(startsOn)
      if (endsOn) dates.push(endsOn)
    }
  })
  if (!dates.length) return null
  dates.sort((a, b) => a - b)
  const startsOn = dates[0]
  const endsOn = dates[dates.length - 1]
  const days = Math.max(0, Math.ceil((startsOn.getTime() - new Date().setHours(0, 0, 0, 0)) / 86400000))
  const dateText = (date) => formatDateTime(date, '').slice(0, 10)
  return { type, label, tone, completed: false, dateRange: `${dateText(startsOn)} ~ ${dateText(endsOn)}`, distanceLabel: days ? '距开始' : '当前状态', distanceValue: days ? `${days} 天` : '进行中' }
}
function alertIconKind(alert) {
  const type = `${alert.typeCode || ''} ${alert.type || ''}`
  if (/湿度|moisture/.test(type)) return 'moisture'
  if (/任务|巡园|逾期/.test(type)) return 'task'
  if (/设备|离线|故障|灌溉失败/.test(type)) return 'device'
  return 'warning'
}
function alertTone(alert) { return ['device', 'warning'].includes(alertIconKind(alert)) ? 'critical' : 'caution' }
function latestAlertTitle(alert) { return `${alert.plotName || '未知地块'} · ${alert.type || '异常告警'}` }
function alertTimeLabel(value) {
  const date = parseDate(value)
  if (!date) return '-'
  const today = new Date()
  const dayKey = (item) => `${item.getFullYear()}-${item.getMonth()}-${item.getDate()}`
  if (dayKey(date) === dayKey(today)) return formatDateTime(date, '').slice(11, 16)
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  if (dayKey(date) === dayKey(yesterday)) return '昨天'
  return formatDateTime(date, '').slice(date.getFullYear() === today.getFullYear() ? 5 : 0, 10)
}
function goToAlerts(alert) {
  router.push({ path: '/farm/alerts', query: alert?.alertId ? { alertId: alert.alertId } : {} })
}
function goToTasks() { router.push('/farm/production') }
function goToRecords() { router.push('/farm/records') }
function goToStatus(plot) {
  if (!plot.deviceOnline) ElMessage.warning(`${plot.plotName} 设备离线，请先检查设备状态`)
  router.push({ path: '/farm/status', query: { plotId: plot.plotId } })
}
</script>

<style scoped>
.dashboard { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.overview-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; margin: 4px 4px 24px; }.overview-head h1 { display: flex; align-items: center; flex-wrap: wrap; margin: 0; color: #155c43; font-size: 34px; font-weight: 800; line-height: 1.25; }.overview-head>div>p { margin: 9px 0 0; color: #65746e; font-size: 15px; }.greeting-weather { display: inline-grid; width: 34px; height: 34px; place-items: center; margin-left: 10px; color: #f1aa13; font-size: 31px; }.update-status { display: flex; align-items: center; gap: 10px; padding-top: 8px; color: #78867f; font-size: 12px; white-space: nowrap; }.update-status button { width: 30px; height: 30px; display: grid; place-items: center; padding: 0; border: 0; color: #23795a; background: transparent; font-size: 22px; cursor: pointer; }.update-status button:disabled { cursor: wait; opacity: .6; }.rotating { animation: rotate .8s linear infinite; }@keyframes rotate { to { transform: rotate(360deg); } }
.stat-row { margin-bottom: 22px; }.stat-row>.el-col { display: flex; }.stat-card { width: 100%; min-height: 190px; display: grid; flex: 1; grid-template-columns: 64px minmax(0,1fr); align-items: start; gap: 18px; margin-bottom: 12px; padding: 26px 22px 21px; border: 1px solid var(--line); border-radius: 16px; background: #fff; box-shadow: 0 8px 28px rgba(20, 69, 53, .05); }.stat-icon { width: 64px; height: 64px; display: grid; place-items: center; border-radius: 16px; color: #147249; background: #edf6eb; font-size: 35px; }.plot-grid-icon { width: 34px; height: 34px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; }.plot-grid-icon span { border: 3px solid currentColor; border-radius: 3px; background: transparent; }.stage-calendar-icon { position: relative; width: 38px; height: 38px; }.stage-calendar-icon::before { position: absolute; top: 5px; left: 0; width: 31px; height: 28px; box-sizing: border-box; border: 3px solid currentColor; border-radius: 3px; content: ''; }.stage-calendar-icon::after { position: absolute; top: 13px; left: 3px; width: 25px; border-top: 3px solid currentColor; content: ''; }.calendar-pins::before, .calendar-pins::after { position: absolute; z-index: 1; top: 1px; width: 3px; height: 10px; border-radius: 2px; background: currentColor; content: ''; }.calendar-pins::before { left: 8px; }.calendar-pins::after { left: 21px; }.calendar-clock { position: absolute; z-index: 2; right: 0; bottom: 0; width: 18px; height: 18px; box-sizing: border-box; border: 3px solid currentColor; border-radius: 50%; background: #edf6eb; }.calendar-clock::before { position: absolute; top: 3px; left: 6px; width: 2px; height: 5px; border-radius: 2px; background: currentColor; content: ''; }.calendar-clock::after { position: absolute; top: 7px; left: 6px; width: 5px; height: 2px; border-radius: 2px; background: currentColor; content: ''; transform: rotate(38deg); transform-origin: left center; }.task-completion-icon { position: relative; width: 34px; height: 38px; }.task-completion-icon::before { position: absolute; top: 4px; left: 2px; width: 30px; height: 32px; box-sizing: border-box; border: 3px solid currentColor; border-radius: 3px; content: ''; }.clipboard-clip { position: absolute; z-index: 1; top: 0; left: 10px; width: 16px; height: 9px; box-sizing: border-box; border: 3px solid currentColor; border-radius: 3px; background: #edf6eb; }.clipboard-check { position: absolute; z-index: 1; top: 14px; left: 11px; width: 9px; height: 15px; border-right: 4px solid currentColor; border-bottom: 4px solid currentColor; transform: rotate(45deg); }.alert-warning-icon { width: 40px; height: 38px; overflow: visible; }.alert-warning-icon path { fill: none; stroke: currentColor; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }.alert-warning-icon circle { fill: currentColor; }.stat-content { min-width: 0; }.stat-label { display: block; margin: 1px 0 9px; color: #4e5d57; font-size: 14px; font-weight: 650; }.stat-value { display: block; color: #126f46; font-size: 29px; font-weight: 800; line-height: 1.2; white-space: nowrap; }.stat-value em { font-size: 14px; font-style: normal; font-weight: 650; }.stat-content p { margin: 18px 0 0; color: #626e69; font-size: 12px; white-space: nowrap; }.stat-content p i { display: inline-block; width: 1px; height: 12px; margin: 0 8px -2px; background: #d7ded9; }.stage-value { display: flex; align-items: flex-start; gap: 9px; }.stage-main { min-width: 0; display: flex; flex: 1; flex-wrap: wrap; gap: 2px 8px; color: #126f46; font-size: 24px; font-weight: 800; line-height: 1.25; }.stage-name { min-width: 0; overflow-wrap: anywhere; }.stage-value>span { flex: 0 0 auto; padding: 4px 9px; border-radius: 999px; color: #337a56; background: #eaf5eb; font-size: 11px; }.stage-period { grid-column: 1 / -1; margin: 5px 0 0; color: #626e69; font-size: 12px; line-height: 1.5; text-align: left; }.stat-content .trend { margin-top: 10px; color: #626e69; }.stat-content .trend strong { margin-left: 4px; color: #22a447; font-size: 14px; }.alert-stat-card .stat-icon { color: #e6372f; background: #fff0ef; }.alert-stat-card .stat-value { color: #e6372f; }.alert-stat-card .alert-breakdown { display: flex; align-items: center; flex-wrap: wrap; gap: 0; white-space: normal; }.alert-stat-card .alert-breakdown i { flex: 0 0 1px; }.alert-stat-card .alert-trend { margin-top: 10px; color: #626e69; }.alert-stat-card .alert-trend strong { margin-left: 4px; color: #ef312d; font-size: 14px; }
.plot-status-card { margin-bottom: 20px; overflow: hidden; border: 1px solid var(--line); border-radius: 16px; background: #fff; box-shadow: 0 8px 28px rgba(20,69,53,.05); }.plot-status-head { display: flex; align-items: center; justify-content: space-between; gap: 22px; padding: 20px 22px; }.plot-status-head h2 { display: flex; align-items: center; gap: 9px; margin: 0; color: #243c33; font-size: 18px; }.plot-status-head h2 .el-icon { color: #188352; font-size: 24px; }.plot-status-tools { display: flex; align-items: center; gap: 12px; }.plot-status-tools .el-input { width: 340px; }.plot-status-tools :deep(.el-input__wrapper),.plot-status-tools :deep(.el-button) { min-height: 40px; border-radius: 8px; }.column-options { display: grid; gap: 3px; }.column-options :deep(.el-checkbox) { margin-right: 0; }.plot-status-table { width: calc(100% - 36px); margin: 0 18px; }.plot-status-table::before { display: none; }.plot-status-table :deep(.el-table__header th) { height: 54px; color: #53645d; background: #f7f9f7; font-size: 12px; font-weight: 700; }.plot-status-table :deep(.el-table__row td) { height: 64px; color: #4e6058; font-size: 12px; }.plot-status-table :deep(.el-table__cell) { border-bottom-color: #edf1ee; }.table-plot-name { color: #273e35; font-size: 13px; }.humidity-value { font-size: 15px; }.humidity-value.success { color: #219449; }.humidity-value.warning { color: #ee941c; }.humidity-value.danger { color: #ed3e35!important; }.irrigation-advice { display: inline-flex; align-items: center; min-height: 28px; padding: 0 10px; border-radius: 7px; font-weight: 650; white-space: nowrap; }.irrigation-advice.success { color: #278753; background: #edf8ef; }.irrigation-advice.warning { color: #e98b18; background: #fff6e8; }.irrigation-advice.danger { color: #d94b45; background: #fff0ef; }.device-state { display: inline-flex; align-items: center; gap: 7px; white-space: nowrap; }.device-state i { width: 9px; height: 9px; border-radius: 50%; background: #16934f; }.device-state.offline i { background: #ef3631; }.pending-count { color: #e89015; font-size: 14px; }.pending-count.danger { color: #ec3d35!important; }.plot-status-table :deep(.el-button--primary.is-link) { color: #238454; font-weight: 650; }.plot-table-footer { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 16px; min-height: 72px; padding: 10px 22px; color: #64756d; font-size: 12px; }.plot-table-footer .el-pagination { justify-self: center; }.plot-table-footer .el-select { width: 104px; justify-self: end; }.plot-table-footer :deep(.el-select__wrapper) { min-height: 34px; border-radius: 7px; }.plot-table-footer :deep(.el-pager li.is-active) { background: #197b51; }
.dashboard-main-grid { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(340px, 1fr); align-items: stretch; gap: 18px; margin-bottom: 20px; }.dashboard-main-grid .plot-status-card { height: 100%; margin-bottom: 0; }.dashboard-main-grid .plot-status-head { flex-wrap: wrap; gap: 14px; }.dashboard-main-grid .plot-status-tools { margin-left: auto; }.dashboard-main-grid .plot-status-tools .el-input { width: clamp(210px, 18vw, 300px); }
.latest-alerts-card { min-width: 0; padding: 22px; border: 1px solid var(--line); border-radius: 16px; background: #fff; box-shadow: 0 8px 28px rgba(20,69,53,.05); }.latest-alerts-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 40px; margin-bottom: 14px; }.latest-alerts-head h2 { margin: 0; color: #202d28; font-size: 21px; line-height: 1.2; }.latest-alerts-head button { display: inline-flex; align-items: center; gap: 5px; padding: 6px 0; border: 0; color: #248557; background: transparent; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; }.latest-alerts-head button .el-icon { font-size: 17px; }.latest-alert-list { display: grid; gap: 2px; }.latest-alert-item { width: 100%; min-height: 82px; display: grid; grid-template-columns: 10px 40px minmax(0,1fr) auto; align-items: center; gap: 12px; padding: 13px 15px; border: 0; border-radius: 7px; color: #2c3934; text-align: left; cursor: pointer; transition: filter .15s ease; }.latest-alert-item:hover { filter: brightness(.98); }.latest-alert-item.critical { color: #ef302e; background: #fff3f2; }.latest-alert-item.caution { color: #ff9414; background: #fff7f1; }.latest-alert-dot { width: 9px; height: 9px; border-radius: 50%; background: currentColor; }.latest-alert-icon { display: grid; place-items: center; font-size: 31px; }.latest-alert-copy { min-width: 0; display: grid; gap: 5px; color: #65716c; }.latest-alert-copy strong { overflow: hidden; color: #252f2b; font-size: 15px; line-height: 1.25; text-overflow: ellipsis; white-space: nowrap; }.latest-alert-copy>span { overflow: hidden; font-size: 12px; line-height: 1.35; text-overflow: ellipsis; white-space: nowrap; }.latest-alert-item time { align-self: center; color: #6a7570; font-size: 12px; white-space: nowrap; }.latest-alerts-card :deep(.el-empty) { padding-block: 80px; }
.dashboard-secondary-grid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(320px, .9fr); align-items: stretch; gap: 18px; margin-bottom: 20px; }.task-execution-card { min-width: 0; padding: 22px 24px 24px; border: 1px solid var(--line); border-radius: 16px; background: #fff; box-shadow: 0 8px 28px rgba(20,69,53,.05); }.task-execution-head { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 18px; }.task-execution-head>div { min-width: 0; display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px; }.task-execution-head h2 { margin: 0; color: #202d28; font-size: 21px; line-height: 1.25; }.task-execution-head span { color: #68736e; font-size: 13px; }.task-execution-head button { display: inline-flex; align-items: center; gap: 5px; padding: 6px 0; border: 0; color: #248557; background: transparent; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; }.task-execution-head button .el-icon { font-size: 17px; }.task-execution-metrics { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 14px; }.task-execution-item { min-width: 0; min-height: 112px; display: grid; grid-template-columns: 44px minmax(0,1fr); align-items: center; gap: 11px; padding: 16px 14px; border: 1px solid #e6ebe8; border-radius: 12px; }.task-execution-item svg { width: 42px; height: 42px; fill: none; stroke: currentColor; stroke-width: 2.7; stroke-linecap: round; stroke-linejoin: round; }.task-execution-item.pending,.task-execution-item.completed { color: #19814e; }.task-execution-item.overdue { color: #ef302e; }.task-execution-item>div { min-width: 0; }.task-execution-item span { display: block; color: #69736f; font-size: 13px; white-space: nowrap; }.task-execution-item strong { display: block; margin-top: 7px; color: currentColor; font-size: 25px; line-height: 1.1; white-space: nowrap; }.task-execution-item strong em { color: #313c38; font-size: 12px; font-style: normal; font-weight: 650; }
.key-milestones-card { min-width: 0; padding: 22px 24px 20px; border: 1px solid var(--line); border-radius: 16px; background: #fff; box-shadow: 0 8px 28px rgba(20,69,53,.05); }.key-milestones-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 10px; }.key-milestones-head h2 { margin: 0; color: #202d28; font-size: 21px; line-height: 1.25; }.key-milestones-head button { display: inline-flex; align-items: center; gap: 5px; padding: 6px 0; border: 0; color: #248557; background: transparent; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; }.key-milestones-head button .el-icon { font-size: 17px; }.key-milestones-list { position: relative; display: grid; }.key-milestones-list::before { position: absolute; top: 31px; bottom: 31px; left: 6px; width: 2px; background: #d8e7dd; content: ''; }.key-milestone-item { position: relative; min-width: 0; min-height: 72px; display: grid; grid-template-columns: 14px minmax(0,1fr) auto; align-items: center; gap: 14px; padding: 10px 0; border-top: 1px solid #edf1ee; }.milestone-marker { z-index: 1; width: 12px; height: 12px; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 4px #fff; }.key-milestone-item.green { color: #18814e; }.key-milestone-item.orange { color: #ff9414; }.milestone-copy { min-width: 0; display: grid; gap: 5px; }.milestone-copy strong { overflow: hidden; color: #26312d; font-size: 14px; line-height: 1.3; text-overflow: ellipsis; white-space: nowrap; }.milestone-copy strong em { color: #727d78; font-size: 12px; font-style: normal; font-weight: 500; }.milestone-copy>span { overflow: hidden; color: #6c7772; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }.milestone-distance { display: flex; align-items: baseline; gap: 6px; white-space: nowrap; }.milestone-distance span { color: #6c7772; font-size: 11px; }.milestone-distance strong { color: currentColor; font-size: 21px; }.key-milestones-card :deep(.el-empty) { padding-block: 28px; }
@media (min-width: 1251px) { .stat-row>.el-col:nth-child(1) { flex: 0 0 24%; max-width: 24%; }.stat-row>.el-col:nth-child(2) { flex: 0 0 25%; max-width: 25%; }.stat-row>.el-col:nth-child(3) { flex: 0 0 24%; max-width: 24%; }.stat-row>.el-col:nth-child(4) { flex: 0 0 27%; max-width: 27%; }.stat-card { grid-template-columns: 58px minmax(0,1fr); gap: 14px; padding: 24px 18px 20px; }.stat-icon { width: 58px; height: 58px; border-radius: 14px; }.stat-icon>* { transform: scale(.9); }.stat-label { margin-bottom: 7px; font-size: 13px; }.stat-value { font-size: 27px; }.stat-value em { font-size: 12px; }.stat-content p, .stage-period { font-size: 11px; }.stage-main { font-size: 22px; }.stage-value>span { padding: 3px 7px; font-size: 10px; }.task-stat-card .stat-content p { white-space: normal; } }
@media (max-width: 1250px) { .stat-card { grid-template-columns: 52px minmax(0,1fr); gap: 13px; padding-inline: 17px; }.stat-icon { width: 52px; height: 52px; font-size: 28px; }.stat-content p { white-space: normal; }.task-execution-item { grid-template-columns: 44px minmax(0,1fr); gap: 11px; padding: 16px 13px; }.task-execution-item svg { width: 43px; height: 43px; }.key-milestones-card { padding-inline: 18px; }.key-milestone-item { gap: 10px; }.milestone-distance { align-items: flex-end; flex-direction: column; gap: 1px; } } @media (max-width: 1080px) { .dashboard-main-grid,.dashboard-secondary-grid { grid-template-columns: 1fr; }.latest-alerts-card { min-height: 0; } } @media (max-width: 900px) { .plot-status-head { align-items: stretch; flex-direction: column; }.plot-status-tools { margin-left: 0; }.plot-status-tools .el-input { width: min(100%, 420px); }.plot-table-footer { grid-template-columns: 1fr auto; }.plot-table-footer .el-pagination { grid-column: 1/-1; grid-row: 1; }.plot-table-footer>span { grid-row: 2; }.plot-table-footer .el-select { grid-row: 2; }.task-execution-metrics { grid-template-columns: 1fr; }.task-execution-item { min-height: 112px; } } @media (max-width: 640px) { .overview-head { flex-direction: column; margin-inline: 0; }.overview-head h1 { font-size: 28px; }.update-status { align-self: flex-end; padding-top: 0; }.stat-card { min-height: 150px; padding: 20px 17px; }.plot-status-tools { align-items: stretch; flex-direction: column; }.plot-status-tools .el-input,.plot-status-tools .el-button { width: 100%; }.plot-status-table { width: calc(100% - 24px); margin-inline: 12px; }.latest-alerts-card { padding: 18px 14px; }.latest-alert-item { grid-template-columns: 8px 32px minmax(0,1fr); gap: 9px; padding-inline: 12px; }.latest-alert-item time { display: none; }.latest-alert-icon { font-size: 26px; }.latest-alert-copy strong { font-size: 14px; }.task-execution-card,.key-milestones-card { padding: 18px 14px; }.task-execution-head,.key-milestones-head { align-items: flex-start; flex-direction: column; gap: 6px; }.task-execution-head button,.key-milestones-head button { align-self: flex-end; }.task-execution-item { grid-template-columns: 48px minmax(0,1fr); padding-inline: 18px; }.task-execution-item svg { width: 46px; height: 46px; }.key-milestone-item { grid-template-columns: 14px minmax(0,1fr); }.milestone-distance { grid-column: 2; align-items: baseline; flex-direction: row; justify-self: start; } }
</style>
