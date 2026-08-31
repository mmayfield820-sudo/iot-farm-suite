<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useFarmerStore } from '@/stores/farmer'
import { getPlotProductionContext } from '@/api/production'
import { listTasks } from '@/api/task'

const router = useRouter()
const store = useFarmerStore()
const plot = computed(() => store.currentPlot)
const weather = computed(() => store.weather || { rainProbability: 0 })
const productionContext = ref(null)
const todayTasks = ref([])
const taskLoading = ref(true)

const actionableTasks = computed(() => todayTasks.value
  .filter((task) => !['completed', 'cancelled'].includes(task.status))
  .slice(0, 3))
const latestAlerts = computed(() => store.visibleAlerts
  .filter((item) => ['未处理', '处理中'].includes(item.status))
  .slice(0, 2))
const recommendation = computed(() => {
  if (!plot.value) return null
  const stage = productionContext.value?.stage
  const minimum = stage?.moistureMin ?? plot.value.threshold
  const maximum = stage?.moistureMax ?? null
  const humidity = Number(plot.value.humidity ?? 0)
  const needsWater = humidity < minimum
  const tooWet = maximum !== null && humidity > maximum
  const unavailable = !plot.value.deviceOnline
  let action = '暂不需要灌溉'
  let tone = 'normal'
  if (plot.value.irrigating) { action = '灌溉进行中'; tone = 'info' }
  else if (needsWater && unavailable) { action = '请先检查灌溉设备'; tone = 'danger' }
  else if (needsWater && weather.value.rainProbability < 40) { action = '建议短时灌溉'; tone = 'warning' }
  else if (needsWater) { action = '暂缓灌溉，关注降雨'; tone = 'warning' }
  else if (tooWet) { action = '土壤湿度偏高，暂不灌溉'; tone = 'info' }
  return {
    action,
    tone,
    duration: Math.min(20, plot.value.irrigationDuration ?? plot.value.maxDuration ?? 30),
    current: humidity,
    target: maximum === null ? `不低于 ${minimum}%` : `${minimum}% - ${maximum}%`,
    stageName: stage?.name || plot.value.cropStage || '当前生产阶段',
  }
})
const fieldStatus = computed(() => {
  if (!plot.value || !recommendation.value) return []
  return [
    { label: '土壤湿度', value: `${recommendation.value.current}%`, detail: `目标 ${recommendation.value.target}`, tone: recommendation.value.tone === 'warning' ? 'warning' : 'green' },
    { label: '环境温度', value: `${plot.value.temperature ?? '-'}℃`, detail: weather.value.condition || '实时环境数据', tone: 'blue' },
    { label: '灌溉设备', value: plot.value.deviceOnline ? '在线' : '离线', detail: plot.value.irrigating ? '正在灌溉' : '等待指令', tone: plot.value.deviceOnline ? 'green' : 'danger' },
  ]
})

function taskStatus(task) {
  return ({ overdue: '已逾期', in_progress: '进行中', pending: '待处理' })[task.status] || '待处理'
}
function taskTone(task) {
  return task.status === 'overdue' ? 'danger' : task.status === 'in_progress' ? 'warning' : 'normal'
}
async function loadProductionContext(plotId) {
  productionContext.value = null
  if (!plotId) return
  try {
    productionContext.value = await getPlotProductionContext(plotId)
  } catch {
    // The dashboard remains useful when the production profile has not been published yet.
  }
}
async function loadTodayTasks() {
  taskLoading.value = true
  try {
    todayTasks.value = await listTasks({ scope: 'today' })
  } catch {
    todayTasks.value = []
  } finally {
    taskLoading.value = false
  }
}
function openIrrigation() {
  if (!plot.value || !recommendation.value) return
  router.push({
    path: '/farmer/irrigation',
    query: { plotId: plot.value.plotId, suggestedMinutes: String(recommendation.value.duration), source: 'recommendation' },
  })
}
function openTasks() { router.push('/farmer/tasks') }

watch(() => plot.value?.plotId, loadProductionContext, { immediate: true })
onMounted(loadTodayTasks)
</script>

<template>
  <div class="farmer-page dashboard-page">
    <header class="dashboard-head">
      <div>
        <p class="dashboard-kicker">今日工作台</p>
        <h1>{{ plot?.plotName || '我的地块' }}</h1>
        <p class="dashboard-subtitle">{{ plot?.farmName || '当前授权地块' }}<span v-if="productionContext?.plannedPlantingDate"> · 计划定植 {{ productionContext.plannedPlantingDate }}</span><span v-else-if="productionContext?.plantingDate"> · 实际定植 {{ productionContext.plantingDate }}</span><span v-if="recommendation"> · {{ recommendation.stageName }}</span></p>
      </div>
      <el-select v-if="store.accessiblePlots.length > 1" class="dashboard-plot-select" :model-value="store.selectedPlotId" @change="store.selectPlot">
        <el-option v-for="item in store.accessiblePlots" :key="item.plotId" :label="`${item.farmName} · ${item.plotName}`" :value="item.plotId" />
      </el-select>
    </header>

    <template v-if="plot && recommendation">
      <section class="work-grid">
        <article class="content-panel task-panel">
          <div class="section-head task-panel-head">
            <div><h3>今天要做什么</h3><p>优先完成计划内农事，现场工作可在农事页补充登记。</p></div>
            <el-button text type="success" @click="openTasks">查看全部<el-icon><ArrowRight /></el-icon></el-button>
          </div>
          <el-skeleton v-if="taskLoading" :rows="3" animated />
          <div v-else-if="actionableTasks.length" class="today-task-list">
            <button v-for="task in actionableTasks" :key="task.id" class="today-task" @click="openTasks">
              <span :class="['task-state', taskTone(task)]"></span>
              <span class="today-task-copy"><strong>{{ task.title }}</strong><small>{{ task.plotName }} · {{ task.taskType || '农事任务' }}</small></span>
              <span :class="['task-status', taskTone(task)]">{{ taskStatus(task) }}</span>
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
          <el-empty v-else :image-size="54" description="今天没有待办农事" />
        </article>

        <article :class="['content-panel', 'irrigation-card', recommendation.tone]">
          <div class="irrigation-title"><span class="irrigation-icon"><el-icon><Drizzling /></el-icon></span><div><p>灌溉建议</p><h2>{{ recommendation.action }}</h2></div></div>
          <dl class="irrigation-facts"><div><dt>当前湿度</dt><dd>{{ recommendation.current }}%</dd></div><div><dt>目标范围</dt><dd>{{ recommendation.target }}</dd></div><div><dt>天气</dt><dd>降雨 {{ weather.rainProbability ?? 0 }}%</dd></div></dl>
          <el-button type="success" @click="openIrrigation">{{ plot.irrigating ? '查看灌溉状态' : '查看并处理' }}</el-button>
        </article>
      </section>

      <section class="field-status" aria-label="当前地块状态">
        <article v-for="item in fieldStatus" :key="item.label" :class="['field-status-item', item.tone]">
          <span class="field-status-dot"></span><div><span>{{ item.label }}</span><strong>{{ item.value }}</strong><small>{{ item.detail }}</small></div>
        </article>
        <button class="field-detail-link" @click="router.push('/farmer/management')">查看地块详情<el-icon><ArrowRight /></el-icon></button>
      </section>

      <section v-if="latestAlerts.length" class="content-panel notice-panel">
        <div class="section-head"><div><h3>需要关注</h3><p>异常会影响今天的灌溉和农事安排。</p></div><el-button text type="success" @click="router.push('/farmer/alarm')">告警中心<el-icon><ArrowRight /></el-icon></el-button></div>
        <div class="notice-list"><button v-for="alert in latestAlerts" :key="alert.alertId" class="notice-item" @click="router.push('/farmer/alarm')"><span class="notice-icon"><el-icon><Warning /></el-icon></span><span><strong>{{ alert.plotName }} · {{ alert.type }}</strong><small>{{ alert.reason }}</small></span><el-icon><ArrowRight /></el-icon></button></div>
      </section>
    </template>

    <el-empty v-else description="暂无可用地块" />
  </div>
</template>

<style scoped>
.dashboard-page{max-width:1220px}.dashboard-head{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:18px}.dashboard-kicker{margin:0 0 6px;color:#378363;font-size:12px;font-weight:700}.dashboard-head h1{margin:0;color:#203b31;font-size:26px;line-height:1.25}.dashboard-subtitle{margin:7px 0 0;color:#778981;font-size:13px}.dashboard-plot-select{width:240px}.work-grid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(310px,.85fr);gap:18px;margin-bottom:18px}.task-panel{min-height:248px}.task-panel-head{margin-bottom:12px}.today-task-list{display:grid}.today-task{display:grid;grid-template-columns:9px minmax(0,1fr) auto 14px;align-items:center;gap:12px;width:100%;min-height:56px;padding:9px 2px;border:0;border-top:1px solid #edf2ef;color:inherit;background:transparent;text-align:left;cursor:pointer}.today-task:first-child{border-top:0}.today-task:hover strong{color:#25815d}.task-state{width:8px;height:8px;border-radius:50%;background:#7bab92}.task-state.warning{background:#d99235}.task-state.danger{background:#ca6262}.today-task-copy{min-width:0}.today-task-copy strong,.today-task-copy small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.today-task-copy strong{color:#29483c;font-size:14px}.today-task-copy small{margin-top:4px;color:#86968f;font-size:11px}.task-status{padding:4px 7px;border-radius:6px;color:#5c776c;background:#f0f5f2;font-size:11px}.task-status.warning{color:#a46d28;background:#fff3df}.task-status.danger{color:#b84f4f;background:#fceaea}.today-task>.el-icon{color:#a3b2ac}.irrigation-card{display:flex;flex-direction:column;border-color:#d8e9df;background:#f7fcf9}.irrigation-card.warning{border-color:#f0dfc4;background:#fffdf8}.irrigation-card.danger{border-color:#efd4d4;background:#fffafa}.irrigation-title{display:flex;align-items:flex-start;gap:12px}.irrigation-icon{width:42px;height:42px;display:grid;place-items:center;flex:0 0 42px;border-radius:11px;color:#277e5b;background:#dff2e7;font-size:21px}.irrigation-card.warning .irrigation-icon{color:#af742b;background:#fff0d8}.irrigation-card.danger .irrigation-icon{color:#bd5858;background:#fbe7e7}.irrigation-title p{margin:1px 0 5px;color:#668176;font-size:12px;font-weight:650}.irrigation-title h2{margin:0;color:#234537;font-size:20px;line-height:1.3}.irrigation-facts{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:18px 0}.irrigation-facts div{min-width:0}.irrigation-facts dt{color:#8a9993;font-size:10px}.irrigation-facts dd{margin:5px 0 0;overflow:hidden;color:#355548;font-size:13px;font-weight:650;text-overflow:ellipsis;white-space:nowrap}.irrigation-card>.el-button{width:100%;margin-top:auto}.field-status{display:grid;grid-template-columns:repeat(3,minmax(0,1fr)) auto;align-items:stretch;margin-bottom:18px;border:1px solid var(--line);border-radius:10px;background:#fff;box-shadow:0 5px 18px rgba(20,69,53,.035)}.field-status-item{display:flex;align-items:center;gap:11px;min-width:0;padding:14px 16px;border-right:1px solid #edf2ef}.field-status-item>div{min-width:0}.field-status-item span:not(.field-status-dot),.field-status-item strong,.field-status-item small{display:block}.field-status-item span:not(.field-status-dot){color:#81918a;font-size:11px}.field-status-item strong{margin:3px 0;color:#29473d;font-size:16px}.field-status-item small{overflow:hidden;color:#99a6a1;font-size:10px;text-overflow:ellipsis;white-space:nowrap}.field-status-dot{width:8px;height:8px;flex:0 0 8px;border-radius:50%;background:#43a477;box-shadow:0 0 0 4px #e6f5ed}.field-status-item.warning .field-status-dot{background:#dd983e;box-shadow:0 0 0 4px #fff3e3}.field-status-item.danger .field-status-dot{background:#ca6262;box-shadow:0 0 0 4px #fceaea}.field-status-item.blue .field-status-dot{background:#4e93b4;box-shadow:0 0 0 4px #eaf4f8}.field-detail-link{display:flex;align-items:center;gap:5px;padding:0 17px;border:0;color:#2b805d;background:transparent;font-size:12px;font-weight:650;white-space:nowrap;cursor:pointer}.field-detail-link:hover{background:#f4faf7}.notice-panel{margin-bottom:18px}.notice-list{display:grid;gap:8px}.notice-item{display:grid;grid-template-columns:38px minmax(0,1fr) 14px;align-items:center;gap:12px;width:100%;padding:10px;border:1px solid #edf1ef;border-radius:8px;color:inherit;background:#fff;text-align:left;cursor:pointer}.notice-item:hover{border-color:#c5dfd0;background:#fbfefc}.notice-icon{width:38px;height:38px;display:grid;place-items:center;border-radius:9px;color:#b87837;background:#fff2e2}.notice-item span:nth-child(2){min-width:0}.notice-item strong,.notice-item small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.notice-item strong{color:#3a5349;font-size:13px}.notice-item small{margin-top:4px;color:#899790;font-size:11px}.notice-item>.el-icon{color:#a7b6af}@media(max-width:900px){.work-grid{grid-template-columns:1fr}.field-status{grid-template-columns:repeat(3,1fr)}.field-detail-link{grid-column:1/-1;justify-content:center;min-height:42px;border-top:1px solid #edf2ef}}@media(max-width:620px){.dashboard-head{align-items:stretch;flex-direction:column}.dashboard-plot-select{width:100%}.field-status{grid-template-columns:1fr}.field-status-item{border-right:0;border-bottom:1px solid #edf2ef}.field-detail-link{grid-column:auto;border-top:0}.irrigation-facts{grid-template-columns:repeat(3,minmax(0,1fr))}.content-panel{padding:16px}}@media(max-width:390px){.irrigation-facts{grid-template-columns:1fr 1fr}.irrigation-facts div:last-child{grid-column:1/-1}}
</style>
