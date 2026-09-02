<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Cloudy, Drizzling, Lightning, PartlyCloudy, Pouring, Sunny } from '@element-plus/icons-vue'
import { getIrrigationRecommendation } from '@/api/irrigationSettings'
import { getPlotProductionContext } from '@/api/production'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'
import { formatDateTime, parseDate } from '@/utils/dataAdapters'

const store = useFarmerStore()
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
const control = reactive({ loading: false, state: 'idle', message: '请选择操作后确认下发。' })
const activeCommand = ref(null)
const plannedDuration = ref(20)
const productionContext = ref(null)
const recommendationData = ref(null)
const recommendationLoading = ref(false)
const controlSection = ref(null)
const autoConfirmOpen = ref(false)
const autoMaxRuntime = ref(30)
let statusRefreshTimer = null
let recommendationRefreshTimer = null
let recommendationRequestToken = 0
let statusRefreshInFlight = false
const plot = computed(() => store.currentPlot)
const controlDevice = computed(() => plot.value?.devices?.irrigation || null)
const controlOnline = computed(() => Boolean(controlDevice.value && (controlDevice.value.online ?? plot.value?.deviceOnline)))
const records = computed(() => {
  const commands = store.farmRecords
    .filter((item) => item.plotId === plot.value?.plotId)
    .slice()
    .sort((left, right) => (parseDate(left.startTime)?.getTime() || 0) - (parseDate(right.startTime)?.getTime() || 0))

  return commands.flatMap((command, index) => {
    if (command.operationType !== '开启') return []
    if (command.status !== '成功') {
      if (['进行中', '待确认'].includes(command.status)) return []
      return [{ ...command, operationType: '灌溉', duration: 0 }]
    }

    const closingCommand = commands.slice(index + 1).find((candidate) => (
      candidate.deviceId === command.deviceId
      && ['开启', '关闭'].includes(candidate.operationType)
      && candidate.status === '成功'
    ))
    if (!closingCommand || closingCommand.operationType !== '关闭') return []

    const startedAt = parseDate(command.startTime)
    const endedAt = parseDate(closingCommand.endTime || closingCommand.startTime)
    const duration = startedAt && endedAt
      ? Math.max(0, Math.round((endedAt.getTime() - startedAt.getTime()) / 60000))
      : command.duration
    return [{
      ...command,
      operationType: '灌溉',
      endTime: closingCommand.endTime || closingCommand.startTime,
      duration,
      status: '成功',
    }]
  }).sort((left, right) => (parseDate(right.startTime)?.getTime() || 0) - (parseDate(left.startTime)?.getTime() || 0))
})
const weather = computed(() => store.weather)
const targetMin = computed(() => {
  const value = Number(productionContext.value?.stage?.moistureMin ?? plot.value?.threshold ?? 0)
  return Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : 0
})
const targetMax = computed(() => {
  const value = Number(productionContext.value?.stage?.moistureMax)
  return Number.isFinite(value) && value > targetMin.value
    ? Math.min(100, value)
    : Math.min(100, targetMin.value + 15)
})
const moistureStatus = computed(() => {
  const humidity = Number(plot.value?.humidity)
  if (humidity < targetMin.value) return '偏低'
  if (humidity > targetMax.value) return '偏高'
  return '适宜'
})
const moistureUpdatedAt = computed(() => {
  const date = parseDate(plot.value?.updateTime || plot.value?.lastHeartbeat)
  if (!date) return '暂无数据'
  const now = new Date()
  const time = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).format(date)
  const dateKey = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
  })
  return dateKey.format(date) === dateKey.format(now) ? `今天 ${time}` : `${dateKey.format(date)} ${time}`
})
const recommendedDuration = computed(() => Number(recommendationData.value?.suggestedMinutes) || 0)
const autoTargetMin = computed(() => Number(recommendationData.value?.inputs?.targetMin ?? targetMin.value))
const autoTargetMax = computed(() => Number(recommendationData.value?.inputs?.targetMax ?? targetMax.value))
const recommendation = computed(() => {
  if (recommendationLoading.value && !recommendationData.value) return { decision: 'loading', state: 'active', title: '正在计算建议', reason: '正在综合当前阶段、土壤湿度、天气、近期灌溉记录和设备状态' }
  const data = recommendationData.value
  if (!data) return { decision: 'check_data', state: 'danger', title: '建议服务暂不可用', reason: '暂时无法完成规则计算，请稍后重试' }
  const state = ({ irrigate: 'warning', check_device: 'danger', check_data: 'danger', active: 'active', wait: 'success', no_irrigation: 'success' })[data.decision] || 'active'
  return { ...data, state, reason: data.summary || data.reasons?.join('；') || '暂无建议依据' }
})
const recommendationUnavailable = computed(() => ['check_device', 'check_data', 'wait'].includes(recommendation.value.decision))
const weatherTemperature = computed(() => {
  const value = Number(weather.value?.temperature)
  if (!Number.isFinite(value)) return '--'
  return Number.isInteger(value) ? value : value.toFixed(1)
})
const weatherIconFor = (value) => {
  const condition = String(value || '')
  if (condition.includes('雷')) return 'lightning'
  if (/大雨|暴雨/.test(condition)) return 'pouring'
  if (/雨|毛毛雨/.test(condition)) return 'drizzling'
  if (condition.includes('多云')) return 'partly-cloudy'
  if (/阴|雾|雪/.test(condition)) return 'cloudy'
  return 'sunny'
}
const weatherIconComponents = { sunny: Sunny, 'partly-cloudy': PartlyCloudy, cloudy: Cloudy, drizzling: Drizzling, pouring: Pouring, lightning: Lightning }
const weatherIcon = computed(() => weatherIconFor(weather.value?.condition))
const weatherForecast = computed(() => (weather.value?.daily || []).slice(1, 5).map((item) => {
  const parts = String(item.date || item.time || '').split('-')
  return {
    ...item,
    dateLabel: parts.length === 3 ? `${Number(parts[1])}/${Number(parts[2])}` : (item.date || item.time || '-'),
    icon: weatherIconFor(item.condition || item.weather),
  }
}))
const suggestedEntry = computed(() => route.query.source === 'recommendation' && typeof route.query.suggestedMinutes === 'string')
const maxDuration = computed(() => Math.max(1, Number(plot.value?.safetyMaxDuration ?? 120)))
const canControl = computed(() => userStore.can('irrigation_record', 'control'))
const startDisabled = computed(() => !canControl.value || !controlOnline.value || plot.value?.irrigating)
const stopDisabled = computed(() => !canControl.value || !controlOnline.value || !plot.value?.irrigating)
const irrigationState = computed(() => {
  if (!controlOnline.value) return { code: 'offline', title: '设备离线', description: '灌溉控制器离线或未绑定' }
  if (plot.value?.irrigating) return { code: 'running', title: '正在灌溉', description: '灌溉设备运行中' }
  return { code: 'ready', title: '未灌溉', description: '设备就绪，可执行灌溉' }
})
const commandLabel = computed(() => ({ idle: '等待操作', sending: '正在下发', executing: '等待设备响应', success: '设备已确认', failed: '执行失败' })[control.state])
const formatTimestamp = (value) => formatDateTime(value, '-')

function adjustDuration(step) {
  plannedDuration.value = Math.max(1, Math.min(maxDuration.value, plannedDuration.value + step))
}

async function applyRecommendation() {
  if (!plot.value || recommendation.value.decision !== 'irrigate' || recommendedDuration.value <= 0) return
  plannedDuration.value = Math.min(recommendedDuration.value, maxDuration.value)
  autoMaxRuntime.value = plannedDuration.value
  await router.replace({
    name: 'farmer-irrigation',
    query: {
      ...route.query,
      plotId: plot.value.plotId,
      source: 'recommendation',
      suggestedMinutes: String(plannedDuration.value),
    },
    hash: '#irrigation-control',
  })
  await nextTick()
  controlSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  autoConfirmOpen.value = true
}

async function loadProductionContext(plotId) {
  productionContext.value = null
  if (!plotId) return
  try {
    const context = await getPlotProductionContext(plotId)
    if (plot.value?.plotId === plotId) productionContext.value = context
  } catch {
    productionContext.value = null
  }
}

async function loadRecommendation(plotId = plot.value?.plotId) {
  if (!plotId) return
  const requestToken = ++recommendationRequestToken
  recommendationLoading.value = true
  try {
    const result = await getIrrigationRecommendation(plotId)
    if (requestToken === recommendationRequestToken && plot.value?.plotId === plotId) recommendationData.value = result
  } catch {
    if (requestToken === recommendationRequestToken && plot.value?.plotId === plotId) recommendationData.value = null
  } finally {
    if (requestToken === recommendationRequestToken) recommendationLoading.value = false
  }
}

watch(() => plot.value?.plotId, (plotId, previousPlotId) => {
  if (plotId !== previousPlotId) recommendationData.value = null
  loadProductionContext(plotId)
  loadRecommendation(plotId)
}, { immediate: true })
watch(() => plot.value?.humidity, (humidity, previousHumidity) => {
  if (humidity !== previousHumidity && plot.value?.plotId) loadRecommendation(plot.value.plotId)
})
watch(
  () => plot.value?.plotId,
  () => {
    if (!plot.value) return
    const maximum = maxDuration.value
    const suggestedMinutes = Number(route.query.suggestedMinutes)
    plannedDuration.value = route.query.plotId === plot.value.plotId && Number.isFinite(suggestedMinutes) && suggestedMinutes > 0
      ? Math.min(suggestedMinutes, maximum)
      : Math.min(20, maximum)
    control.state = 'idle'
    control.message = '请选择操作后确认下发。'
  },
  { immediate: true },
)
watch(
  [() => route.query.plotId, () => store.farmPlots.length],
  ([plotId]) => {
    if (typeof plotId === 'string' && store.farmPlots.some((item) => item.plotId === plotId)) store.selectPlot(plotId)
  },
  { immediate: true },
)

async function execute(action, options = {}) {
  const verb = action === 'open' ? '开启' : '关闭'
  const activationType = action === 'open' ? (options.activationType || 'manual') : 'manual'
  const durationMinutes = action === 'open' ? Number(options.durationMinutes ?? plannedDuration.value) : null
  const targetMode = activationType === 'auto'
  let commandCompleted = false
  if (!controlDevice.value) return ElMessage.error('当前地块未绑定灌溉控制器')
  if (!controlOnline.value) return ElMessage.error('灌溉控制器离线，禁止远程控制')
  try {
    if (!options.skipConfirmation) {
      await ElMessageBox.confirm(
        `目标地块：${plot.value.plotName}\n控制设备：${controlDevice.value.deviceNo}\n当前湿度：${plot.value.humidity}%\n计划时长：${action === 'open' ? `${durationMinutes} 分钟` : '立即关闭'}\n\n确认${verb}灌溉吗？`,
        `二次确认：${verb}灌溉`,
        { type: action === 'open' ? 'warning' : 'info', confirmButtonText: `确认${verb}`, cancelButtonText: '取消' },
      )
    }
    control.loading = true
    activeCommand.value = store.beginCommand(plot.value.plotId, action, durationMinutes, activationType)
    control.state = 'sending'
    control.message = targetMode ? '正在启动目标湿度自动灌溉…' : `正在下发${verb}灌溉指令…`
    const submitted = await store.sendControl(activeCommand.value)
    control.state = 'executing'
    control.message = '指令已下发，正在等待设备响应…'
    const response = await store.waitCommandResult(submitted.commandId)
    const result = ['success', '成功'].includes(response?.result || response?.status) ? 'success' : response?.status === 'timeout' ? 'timeout' : 'failed'
    store.completeCommand(activeCommand.value.commandId, result, targetMode ? '自动' : '手动')
    commandCompleted = true
    await store.refreshIrrigationRecords(plot.value.plotId)
    await loadRecommendation(plot.value.plotId)
    if (result !== 'success') {
      control.state = 'failed'
      control.message = response?.message || (result === 'timeout' ? '设备未在规定时间内响应' : '设备未能执行该命令')
      ElMessage.error(control.message)
      return
    }
    control.state = 'success'
    control.message = targetMode
      ? `自动灌溉已启动，湿度稳定达到 ${autoTargetMin.value}% 或运行 ${durationMinutes} 分钟后将自动关闭`
      : `${verb}命令已由设备确认执行`
    ElMessage.success(targetMode ? '目标湿度自动灌溉已启动' : `${verb}命令执行成功`)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      if (activeCommand.value && !commandCompleted) store.completeCommand(activeCommand.value.commandId, 'failed', '用户')
      control.state = 'failed'
      control.message = error?.message || '命令执行失败，请稍后重试'
    }
  } finally {
    control.loading = false
  }
}

async function confirmAutoIrrigation() {
  const maximum = Math.max(5, Math.min(maxDuration.value, Number(autoMaxRuntime.value) || recommendedDuration.value))
  autoMaxRuntime.value = maximum
  autoConfirmOpen.value = false
  await execute('open', { activationType: 'auto', durationMinutes: maximum, skipConfirmation: true })
}

onMounted(() => {
  statusRefreshTimer = window.setInterval(async () => {
    if (!plot.value?.plotId || statusRefreshInFlight) return
    const plotId = plot.value.plotId
    statusRefreshInFlight = true
    try {
      await store.refreshIrrigationRecords(plotId)
    } catch {
      // A transient refresh failure must not overwrite the last confirmed state.
    } finally {
      statusRefreshInFlight = false
    }
  }, 2000)
  recommendationRefreshTimer = window.setInterval(() => loadRecommendation().catch(() => {}), 60000)
})

onUnmounted(() => {
  if (statusRefreshTimer) window.clearInterval(statusRefreshTimer)
  if (recommendationRefreshTimer) window.clearInterval(recommendationRefreshTimer)
})
</script>

<template>
  <div class="farmer-page irrigation-page">
    <div class="page-head">
      <div><h1 class="page-title">智慧灌溉</h1><p class="page-subtitle">依据实时农情生成可解释建议，控制操作必须二次确认。</p></div>
      <div class="page-actions"><div class="filter-control plot-filter"><span class="filter-label"><el-icon><Location /></el-icon> 当前地块</span><el-select class="plot-select" size="large" :model-value="store.currentPlot?.plotId" @change="store.selectPlot"><el-option v-for="item in store.farmPlots" :key="item.plotId" :label="item.plotName" :value="item.plotId" /></el-select></div></div>
    </div>

    <template v-if="plot">
      <section class="irrigation-overview">
        <article :class="['overview-cell', 'recommendation-cell', recommendation.state]">
          <span class="overview-label">灌溉建议</span>
          <div class="overview-primary"><span class="overview-icon"><el-icon v-if="recommendation.decision === 'loading'" class="is-loading"><Loading /></el-icon><el-icon v-else-if="recommendationUnavailable"><CircleClose /></el-icon><el-icon v-else><CircleCheck /></el-icon></span><strong>{{ recommendation.title }}</strong></div>
          <p>{{ recommendation.reason }}</p>
          <button v-if="recommendation.decision === 'irrigate'" type="button" class="recommendation-action" @click="applyRecommendation">按目标湿度自动灌溉 <el-icon><ArrowRight /></el-icon></button>
        </article>
        <article class="overview-cell moisture-cell">
          <span class="overview-label">土壤湿度</span>
          <div class="moisture-reading"><strong>{{ plot.humidity }}%</strong><em :class="{ low: moistureStatus === '偏低', high: moistureStatus === '偏高' }">{{ moistureStatus }}</em></div>
          <p class="target-range">目标区间：{{ targetMin }}% ~ {{ targetMax }}%</p>
          <div class="moisture-scale">
            <span class="moisture-progress" :style="{ width: `${Math.max(0, Math.min(100, Number(plot.humidity)))}%` }"></span>
            <i class="target-marker" :style="{ left: `${targetMin}%` }"></i>
            <i class="target-marker" :style="{ left: `${targetMax}%` }"></i>
          </div>
          <div class="scale-labels"><span class="scale-start">0%</span><span :style="{ left: `${targetMin}%` }">{{ targetMin }}%</span><span :style="{ left: `${targetMax}%` }">{{ targetMax }}%</span><span class="scale-end">100%</span></div>
          <p class="moisture-updated">更新时间：{{ moistureUpdatedAt }}</p>
        </article>
        <article :class="['overview-cell', 'device-cell', { offline: !controlOnline }]">
          <span class="overview-label">设备状态</span>
          <div class="overview-primary"><span class="overview-icon"><el-icon v-if="controlOnline"><CircleCheck /></el-icon><span v-else class="device-warning" aria-label="设备异常"><svg viewBox="0 0 48 44" aria-hidden="true"><path d="M21 5.5a3.5 3.5 0 0 1 6 0l17 29.4a3.5 3.5 0 0 1-3 5.3H7a3.5 3.5 0 0 1-3-5.3z"/><path d="M24 15v12"/><circle cx="24" cy="33" r="1.6"/></svg></span></span><strong>{{ controlOnline ? '正常' : '异常' }}</strong></div>
          <p>{{ controlOnline ? '灌溉控制器在线' : '灌溉控制器离线或未绑定' }}</p>
        </article>
        <article class="overview-cell weather-cell">
          <span class="overview-label">天气预报</span>
          <div class="weather-display">
            <span :class="['weather-symbol', weatherIcon]">
              <el-icon v-if="weatherIcon === 'lightning'"><Lightning /></el-icon>
              <el-icon v-else-if="weatherIcon === 'pouring'"><Pouring /></el-icon>
              <el-icon v-else-if="weatherIcon === 'drizzling'"><Drizzling /></el-icon>
              <el-icon v-else-if="weatherIcon === 'partly-cloudy'"><PartlyCloudy /></el-icon>
              <el-icon v-else-if="weatherIcon === 'cloudy'"><Cloudy /></el-icon>
              <el-icon v-else><Sunny /></el-icon>
            </span>
            <div class="weather-reading"><strong>{{ weatherTemperature }}<small>℃</small></strong><p>{{ weather?.condition || '暂无天气数据' }}</p></div>
          </div>
          <div v-if="weatherForecast.length" class="weather-forecast">
            <div v-for="day in weatherForecast" :key="day.date || day.time" class="forecast-day">
              <strong>{{ day.dateLabel }}</strong>
              <span :class="['forecast-icon', day.icon]"><el-icon><component :is="weatherIconComponents[day.icon]" /></el-icon></span>
              <span class="forecast-high">{{ day.high ?? '-' }}℃</span>
              <span class="forecast-low">{{ day.low ?? '-' }}℃</span>
            </div>
          </div>
        </article>
      </section>

      <section id="irrigation-control" ref="controlSection" class="content-panel irrigation-control">
        <div class="control-title"><h3>灌溉控制</h3></div>
        <el-alert v-if="suggestedEntry" title="已按目标湿度模式预填地块和最长运行时间" type="success" :closable="false" show-icon />
        <div class="control-layout">
          <section class="current-state">
            <span class="control-label">当前状态</span>
            <div class="state-body">
              <span :class="['state-visual', irrigationState.code]"><i></i></span>
              <div><strong>{{ irrigationState.title }}</strong><p>{{ irrigationState.description }}</p></div>
            </div>
          </section>
          <section class="duration-control">
            <span class="control-label">设置灌溉时长</span>
            <div class="duration-stepper">
              <button type="button" title="减少时长" :disabled="plannedDuration <= 1" @click="adjustDuration(-5)"><el-icon><Minus /></el-icon></button>
              <div><strong>{{ plannedDuration }}</strong><span>分钟</span></div>
              <button type="button" title="增加时长" :disabled="plannedDuration >= maxDuration" @click="adjustDuration(5)"><el-icon><Plus /></el-icon></button>
            </div>
            <div class="duration-presets">
              <button v-for="minutes in [10, 20, 30]" :key="minutes" type="button" :class="{ active: plannedDuration === minutes }" :disabled="minutes > maxDuration" @click="plannedDuration = minutes">{{ minutes }} 分钟</button>
              <el-popover placement="bottom" :width="210" trigger="click">
                <el-input-number v-model="plannedDuration" :min="1" :max="maxDuration" controls-position="right" />
                <template #reference><button type="button" :class="{ active: ![10, 20, 30].includes(plannedDuration) }">自定义</button></template>
              </el-popover>
            </div>
            <div class="control-actions">
              <el-button type="success" size="large" :loading="control.loading" :disabled="startDisabled" @click="execute('open')"><el-icon><VideoPlay /></el-icon>开始灌溉</el-button>
              <el-button size="large" :loading="control.loading" :disabled="stopDisabled" @click="execute('close')"><span class="stop-icon"></span>关闭灌溉</el-button>
            </div>
          </section>
        </div>
        <div v-if="control.state !== 'idle'" :class="['command-feedback', control.state]"><span :class="['feedback-dot', control.state]"></span><strong>{{ commandLabel }}</strong><p>{{ control.message }}</p></div>
      </section>

      <section class="content-panel record-panel">
        <div class="section-head"><div><h3>灌溉执行记录</h3><p>查看当前地块的操作人、执行时间与结果。</p></div></div>
        <el-table :data="records" class="compact-table">
          <el-table-column label="开始时间" min-width="165"><template #default="scope">{{ formatTimestamp(scope.row.startTime) }}</template></el-table-column>
          <el-table-column label="结束时间" min-width="165"><template #default="scope">{{ scope.row.endTime ? formatTimestamp(scope.row.endTime) : '进行中' }}</template></el-table-column>
          <el-table-column prop="operationType" label="操作" width="80" />
          <el-table-column label="时长" width="110"><template #default="scope">{{ scope.row.duration }} 分钟</template></el-table-column>
          <el-table-column prop="operator" label="执行人" width="100" />
          <el-table-column prop="status" label="状态" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === '失败' ? 'danger' : scope.row.status === '进行中' ? 'info' : '']">{{ scope.row.status }}</span></template></el-table-column>
        </el-table>
        <el-empty v-if="!records.length" :image-size="58" description="暂无灌溉记录" />
      </section>
    </template>

    <el-dialog v-model="autoConfirmOpen" title="按目标湿度自动灌溉" width="480px" append-to-body destroy-on-close>
      <div class="auto-confirm-content">
        <dl>
          <div><dt>目标地块</dt><dd>{{ plot?.plotName }}</dd></div>
          <div><dt>当前湿度</dt><dd>{{ plot?.humidity }}%</dd></div>
          <div><dt>目标区间</dt><dd>{{ autoTargetMin }}% ~ {{ autoTargetMax }}%</dd></div>
          <div><dt>停止条件</dt><dd>湿度达到目标区间下限 {{ autoTargetMin }}%</dd></div>
        </dl>
        <label class="auto-runtime-field"><span>最长运行时间</span><el-input-number v-model="autoMaxRuntime" :min="5" :max="maxDuration" :step="5" controls-position="right" /><em>分钟</em></label>
        <p>达到目标湿度后自动关闭；若未达到，将在最长运行时间结束时自动关闭。运行中可随时使用页面上的“关闭灌溉”。</p>
      </div>
      <template #footer><el-button @click="autoConfirmOpen = false">取消</el-button><el-button type="success" :loading="control.loading" :disabled="startDisabled" @click="confirmAutoIrrigation">确认启动</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.irrigation-overview {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  width: 100%;
  min-height: 224px;
  margin-bottom: 18px;
  overflow: hidden;
  border: 1px solid #e8e5d9;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 10px rgba(67, 72, 55, .04);
}

.overview-cell {
  min-width: 0;
  padding: 22px 20px 20px;
  border-right: 1px solid #eeeae0;
}

.overview-cell:last-child {
  border-right: 0;
}

.overview-label {
  display: block;
  margin-bottom: 22px;
  color: #66736c;
  font-size: 14px;
  font-weight: 600;
}

.overview-primary {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 36px;
  margin-bottom: 15px;
}

.overview-primary strong {
  color: #263c32;
  font-size: 19px;
  line-height: 1.35;
}

.overview-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  border-radius: 50%;
  color: #287c59;
  background: #e8f4ed;
  font-size: 20px;
}

.overview-cell p {
  margin: 6px 0 0;
  color: #849087;
  font-size: 12px;
  line-height: 1.65;
}

.device-cell.offline .overview-icon {
  color: #c6554f;
  background: transparent;
}

.recommendation-cell .overview-icon {
  width: 36px;
  height: 36px;
  flex-basis: 36px;
  border-radius: 0;
  color: #247a49;
  background: transparent;
  font-size: 36px;
}

.recommendation-cell .overview-primary strong {
  color: #247a49;
  font-size: 24px;
}

.recommendation-cell.danger .overview-icon,
.recommendation-cell.danger .overview-primary strong {
  color: #c6554f;
}

.overview-cell.recommendation-cell p {
  color: #303c36;
  font-size: 14px;
}

.recommendation-action {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-top: 14px;
  padding: 7px 0;
  border: 0;
  color: #247a49;
  background: transparent;
  font: inherit;
  font-size: 14px;
  font-weight: 650;
  cursor: pointer;
}

.recommendation-action:hover {
  color: #145f36;
}

.recommendation-action .el-icon {
  font-size: 15px;
}

.auto-confirm-content dl {
  margin: 0;
  border-top: 1px solid #edf0ec;
}

.auto-confirm-content dl div {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 11px 2px;
  border-bottom: 1px solid #edf0ec;
}

.auto-confirm-content dt {
  color: #6d7973;
}

.auto-confirm-content dd {
  margin: 0;
  color: #21352b;
  font-weight: 650;
  text-align: right;
}

.auto-runtime-field {
  display: grid;
  grid-template-columns: 1fr 150px auto;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
  color: #34483e;
  font-weight: 650;
}

.auto-runtime-field em {
  color: #64736c;
  font-style: normal;
  font-weight: 400;
}

.auto-confirm-content > p {
  margin: 16px 0 0;
  padding: 11px 13px;
  border-radius: 6px;
  color: #617168;
  background: #f5f8f4;
  font-size: 13px;
  line-height: 1.65;
}

.device-cell .overview-icon {
  width: 36px;
  height: 36px;
  flex-basis: 36px;
  border-radius: 0;
  color: #247a49;
  background: transparent;
  font-size: 36px;
}

.device-cell .overview-primary strong {
  color: #247a49;
  font-size: 24px;
}

.overview-cell.device-cell p {
  color: #303c36;
  font-size: 14px;
}

.device-cell.offline .overview-primary strong {
  color: #c6554f;
}

.device-warning {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: #db7b73;
}

.device-warning svg {
  width: 36px;
  height: 34px;
  overflow: visible;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3.6;
}

.device-warning circle {
  fill: currentColor;
  stroke: none;
}

.moisture-reading {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 15px;
}

.moisture-reading strong {
  color: #277e5b;
  font-size: 28px;
  line-height: 1;
}

.moisture-reading em {
  min-width: 54px;
  padding: 6px 12px;
  border-radius: 7px;
  color: #277e5b;
  background: #edf5dd;
  font-size: 15px;
  font-style: normal;
  line-height: 1.2;
  text-align: center;
}

.moisture-reading em.low {
  color: #b67715;
  background: #fff1cf;
}

.moisture-reading em.high {
  color: #b64f49;
  background: #fbe9e7;
}

.overview-cell .target-range {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 0;
  color: #53635b;
  font-size: 13px;
  white-space: nowrap;
}

.moisture-scale {
  position: relative;
  height: 6px;
  margin-top: 14px;
  border-radius: 3px;
  background: #e5e7e5;
}

.moisture-progress {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #55a87c;
}

.target-marker {
  position: absolute;
  top: -3px;
  width: 1px;
  height: 12px;
  background: #d8ddd6;
  transform: translateX(-50%);
}

.scale-labels {
  position: relative;
  height: 15px;
  margin-top: 7px;
  color: #a1aaa5;
  font-size: 10px;
}

.scale-labels span {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  white-space: nowrap;
}

.scale-labels .scale-start {
  left: 0;
  transform: none;
}

.scale-labels .scale-end {
  right: 0;
  transform: none;
}

.overview-cell .moisture-updated {
  margin-top: 10px;
  color: #9aa39e;
  font-size: 11px;
}

.weather-display {
  display: flex;
  align-items: center;
  gap: 18px;
  min-height: 86px;
  margin-top: 2px;
}

.weather-symbol {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  flex: 0 0 58px;
  font-size: 56px;
}

.weather-symbol.sunny,
.weather-symbol.partly-cloudy {
  color: #efb62f;
}

.weather-symbol.sunny::after {
  position: absolute;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: currentColor;
  content: '';
}

.weather-symbol.cloudy {
  color: #89948e;
}

.weather-symbol.drizzling,
.weather-symbol.pouring {
  color: #4384ae;
}

.weather-symbol.lightning {
  color: #d38b20;
}

.weather-reading strong {
  display: flex;
  align-items: flex-start;
  color: #26372f;
  font-size: 34px;
  line-height: 1;
}

.weather-reading strong small {
  margin: 3px 0 0 3px;
  font-size: 16px;
  font-weight: 600;
}

.overview-cell .weather-reading p {
  margin-top: 8px;
  color: #303c36;
  font-size: 15px;
  font-weight: 600;
}

.weather-forecast {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 2px;
  margin-top: 10px;
}

.forecast-day {
  display: grid;
  justify-items: center;
  min-width: 0;
  color: #34423b;
}

.forecast-day > strong {
  font-size: 12px;
  line-height: 1.3;
  white-space: nowrap;
}

.forecast-icon {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  margin: 5px 0 3px;
  font-size: 28px;
}

.forecast-icon.sunny,
.forecast-icon.partly-cloudy {
  color: #efb62f;
}

.forecast-icon.sunny::after {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: currentColor;
  content: '';
}

.forecast-icon.cloudy {
  color: #89948e;
}

.forecast-icon.drizzling,
.forecast-icon.pouring {
  color: #4384ae;
}

.forecast-icon.lightning {
  color: #d38b20;
}

.forecast-high,
.forecast-low {
  color: #4f5b55;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.45;
  white-space: nowrap;
}

.forecast-high {
  color: #4f5b55;
}

.irrigation-control {
  margin-bottom: 18px;
  padding: 20px 22px 22px;
}

.control-title h3 {
  margin: 0 0 16px;
  color: #202d26;
  font-size: 18px;
}

.irrigation-control > .el-alert {
  margin-bottom: 12px;
}

.control-layout {
  display: grid;
  grid-template-columns: minmax(300px, 2fr) minmax(500px, 3fr);
  min-height: 236px;
  overflow: hidden;
  border: 1px solid #e8e5dc;
  border-radius: 8px;
}

.current-state,
.duration-control {
  min-width: 0;
  padding: 16px 20px;
}

.current-state {
  display: grid;
  grid-template-rows: auto 1fr;
  border-right: 1px solid #e8e5dc;
}

.control-label {
  color: #4e5b54;
  font-size: 13px;
  font-weight: 650;
}

.state-body {
  display: flex;
  align-items: center;
  gap: 22px;
  align-self: stretch;
}

.state-visual {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 92px;
  height: 92px;
  flex: 0 0 92px;
  border-radius: 50%;
  background: #edf5dd;
}

.state-visual i {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  background: #247a49;
}

.state-visual.running {
  background: #e5f3ea;
}

.state-visual.running i {
  border-radius: 50%;
  box-shadow: 0 0 0 7px rgba(36, 122, 73, .12);
}

.state-visual.offline {
  background: #faecea;
}

.state-visual.offline i {
  background: #d87b74;
}

.state-body strong,
.state-body p {
  display: block;
}

.state-body strong {
  color: #247a49;
  font-size: 28px;
  line-height: 1.25;
}

.state-body p {
  margin: 10px 0 0;
  color: #4f5c55;
  font-size: 14px;
}

.current-state:has(.state-visual.offline) .state-body strong {
  color: #c9645d;
}

.duration-control {
  display: flex;
  flex-direction: column;
}

.duration-stepper {
  display: grid;
  grid-template-columns: 44px minmax(170px, 1fr) 44px;
  align-items: center;
  gap: 16px;
  width: min(100%, 520px);
  margin: 4px auto 12px;
}

.duration-stepper button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border: 1px solid #d8ddd7;
  border-radius: 50%;
  color: #247a49;
  background: #fff;
  font-size: 22px;
  cursor: pointer;
}

.duration-stepper button:disabled {
  color: #b9c0bc;
  cursor: not-allowed;
}

.duration-stepper > div {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 11px;
}

.duration-stepper > div::before,
.duration-stepper > div::after {
  width: 62px;
  border-top: 1px solid #e1e5e1;
  content: '';
}

.duration-stepper strong {
  color: #17231d;
  font-size: 40px;
  line-height: 1;
}

.duration-stepper span {
  color: #414d47;
  font-size: 14px;
  white-space: nowrap;
}

.duration-presets,
.control-actions {
  display: grid;
  gap: 12px;
}

.duration-presets {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: auto;
}

.duration-presets button {
  width: 100%;
  height: 38px;
  border: 1px solid #d9ddd8;
  border-radius: 6px;
  color: #4e5a54;
  background: #fff;
  font-size: 13px;
  cursor: pointer;
}

.duration-presets button.active {
  border-color: #4b9168;
  color: #267849;
  background: #f3f8ef;
  font-weight: 650;
  box-shadow: inset 0 0 0 1px rgba(75, 145, 104, .18);
}

.duration-presets button:disabled {
  color: #b5bcb8;
  background: #f7f7f4;
  cursor: not-allowed;
}

.control-actions {
  grid-template-columns: 1fr 1fr;
  margin-top: 16px;
}

.control-actions .el-button {
  width: 100%;
  height: 44px;
  margin: 0;
  font-size: 14px;
  font-weight: 650;
}

.stop-icon {
  width: 12px;
  height: 12px;
  margin-right: 2px;
  border-radius: 2px;
  background: currentColor;
}

.command-feedback {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 11px 13px;
  border-radius: 8px;
  color: #60776c;
  background: #f4f8f6;
  font-size: 12px;
}

.command-feedback strong {
  font-size: 12px;
}

.command-feedback p {
  margin: 0;
  color: #73867d;
}

.feedback-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  border-radius: 50%;
  background: #93a59c;
}

.feedback-dot.sending,
.feedback-dot.executing {
  background: #d69439;
}

.feedback-dot.success {
  background: #38a06f;
}

.feedback-dot.failed {
  background: #c35a5a;
}

.record-panel {
  margin-top: 18px;
}

@media (max-width: 1020px) {
  .irrigation-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .overview-cell:nth-child(2) {
    border-right: 0;
  }

  .overview-cell:nth-child(-n + 2) {
    border-bottom: 1px solid #eeeae0;
  }
}

@media (max-width: 850px) {
  .control-layout {
    grid-template-columns: 1fr;
  }

  .current-state {
    min-height: 190px;
    border-right: 0;
    border-bottom: 1px solid #e8e5dc;
  }
}

@media (max-width: 620px) {
  .irrigation-overview {
    grid-template-columns: 1fr;
    width: 100%;
  }

  .overview-cell,
  .overview-cell:nth-child(2) {
    padding: 20px;
    border-right: 0;
    border-bottom: 1px solid #eeeae0;
  }

  .overview-cell:last-child {
    border-bottom: 0;
  }

  .overview-label {
    margin-bottom: 14px;
  }

  .irrigation-control {
    padding: 18px 14px;
  }

  .current-state,
  .duration-control {
    padding: 16px;
  }

  .state-visual {
    width: 74px;
    height: 74px;
    flex-basis: 74px;
  }

  .state-body strong {
    font-size: 23px;
  }

  .duration-stepper {
    grid-template-columns: 40px minmax(120px, 1fr) 40px;
    gap: 8px;
  }

  .duration-stepper button {
    width: 40px;
    height: 40px;
  }

  .duration-stepper > div::before,
  .duration-stepper > div::after {
    width: 20px;
  }

  .duration-presets,
  .control-actions {
    grid-template-columns: 1fr 1fr;
  }

  .command-feedback {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .command-feedback p {
    width: 100%;
    margin-left: 16px;
  }
}
</style>
