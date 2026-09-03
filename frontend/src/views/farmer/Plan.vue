<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { getPlotProductionContext } from '@/api/production'
import { listTasks } from '@/api/task'
import { useFarmerStore } from '@/stores/farmer'

const store = useFarmerStore()
const router = useRouter()
const loading = ref(false)
const context = ref(null)
const tasks = ref([])
const expandedStages = ref(new Set())
const currentStageCode = computed(() => context.value?.stage?.code)
const activeTasks = computed(() => tasks.value.filter((task) => ['pending', 'in_progress', 'overdue'].includes(task.status)))
const statusLabels = { pending: '待处理', in_progress: '进行中', overdue: '已逾期', completed: '已完成', cancelled: '已取消' }
const statusTypes = { pending: 'warning', in_progress: 'warning', overdue: 'danger', completed: 'success', cancelled: 'info' }
const taskTypeLabels = { inspection: '巡园检查', pruning: '修剪管理', fertilization: '施肥管理', flower_management: '花果管理', fruit_management: '果实管理', irrigation: '灌溉检查', harvest: '采收管理', pest_control: '病虫害防治', cleanup: '清园管理' }

function monthKeys(start, end) {
  if (!start || !end) return [new Date().toISOString().slice(0, 7)]
  const cursor = new Date(`${start.slice(0, 7)}-01T00:00:00`)
  const last = new Date(`${end.slice(0, 7)}-01T00:00:00`)
  const result = []
  while (cursor <= last) {
    result.push(`${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, '0')}`)
    cursor.setMonth(cursor.getMonth() + 1)
  }
  return result
}
function stageWindow(stage) { return stage?.startsOn && stage?.endsOn ? `${stage.startsOn.slice(5)} 至 ${stage.endsOn.slice(5)}` : '日期待配置' }
function isExpanded(code) { return expandedStages.value.has(code) }
function toggleStage(code) {
  const next = new Set(expandedStages.value)
  if (next.has(code)) next.delete(code); else next.add(code)
  expandedStages.value = next
}
function planItemKey(item) { return [item.stageCode, item.taskType, item.title, item.scheduledDate].join('|') }
const completePlanItems = computed(() => {
  const taskQueues = new Map()
  for (const task of tasks.value.filter((item) => item.source === 'template')) {
    const key = planItemKey(task)
    if (!taskQueues.has(key)) taskQueues.set(key, [])
    taskQueues.get(key).push(task)
  }
  return (context.value?.planItems || []).map((item, index) => {
    const matched = taskQueues.get(planItemKey(item))?.shift()
    return matched || { ...item, id: `plan-${item.stageCode}-${index}`, status: null }
  })
})
const stageGroups = computed(() => (context.value?.stages || []).map((stage) => ({
  ...stage,
  tasks: completePlanItems.value.filter((task) => task.stageCode === stage.code).sort((a, b) => a.scheduledDate.localeCompare(b.scheduledDate)),
})))

async function loadPlan() {
  if (!store.selectedPlotId) return
  loading.value = true
  try {
    const nextContext = await getPlotProductionContext(store.selectedPlotId)
    context.value = nextContext
    const months = monthKeys(nextContext.productionYearStartsOn, nextContext.productionYearEndsOn)
    const rows = await Promise.all(months.map((month) => listTasks({ scope: 'month', month, plotId: store.selectedPlotId })))
    tasks.value = rows.flat()
    expandedStages.value = new Set(nextContext.stage?.code ? [nextContext.stage.code] : [])
  } catch (error) {
    context.value = null
    tasks.value = []
    ElMessage.error(error.message || '管理计划加载失败')
  } finally { loading.value = false }
}
watch(() => store.selectedPlotId, loadPlan, { immediate: true })
</script>

<template>
  <div class="farmer-page plan-page" v-loading="loading">
    <header class="plan-hero"><div><h1 class="page-title">脐橙全周期管理</h1><p>从萌芽、开花到成熟采收，将每个阶段的农事安排整理成清晰的生长档案。</p></div><el-select :model-value="store.selectedPlotId" class="plot-select" @change="store.selectPlot"><el-option v-for="plot in store.accessiblePlots" :key="plot.plotId" :label="plot.plotName" :value="plot.plotId" /></el-select></header>
    <section class="plan-overview">
      <div><span>当前阶段</span><strong>{{ context?.stage?.name || '暂无法判断' }}</strong><small>{{ context?.stage?.managementFocus || '等待生产周期资料' }}</small></div>
      <div><span>品种模板</span><strong>{{ context?.templateName || '尚未绑定模板' }}</strong><small>{{ context?.crop || '-' }} · V{{ context?.versionNo || '-' }}</small></div>
      <div class="metric"><span>全年计划</span><strong>{{ completePlanItems.length }}</strong><small>其中 {{ activeTasks.length }} 项待执行</small></div>
      <el-button class="plan-action" type="success" plain @click="router.push('/farmer/tasks')">进入我的农事</el-button>
    </section>
    <section class="cycle-panel">
      <div class="section-title"><div><h2>分阶段农事计划</h2><p>{{ context?.productionYearStartsOn || '-' }} 至 {{ context?.productionYearEndsOn || '-' }}</p></div><em>共 {{ stageGroups.length }} 个阶段</em></div>
      <el-empty v-if="!stageGroups.length" description="暂无生产周期计划" />
      <div v-else class="stage-list"><article v-for="stage in stageGroups" :key="stage.code" :class="['stage-block', { current: stage.code === currentStageCode, expanded: isExpanded(stage.code) }]">
        <div class="stage-rail"><span>{{ stage.name?.slice(0, 1) || '事' }}</span></div>
        <div class="stage-content"><button class="stage-head" type="button" :aria-expanded="isExpanded(stage.code)" @click="toggleStage(stage.code)"><div><div class="stage-name"><h3>{{ stage.name }}</h3><el-tag v-if="stage.code === currentStageCode" type="success">当前阶段</el-tag></div><p>{{ stage.managementFocus || '按模板落实阶段农事与巡园观察' }}</p><small>{{ stage.tasks.length }} 项农事安排</small></div><span class="stage-date"><span>{{ stageWindow(stage) }}</span><el-icon class="stage-arrow"><ArrowDown /></el-icon></span></button>
          <div v-if="isExpanded(stage.code)" class="stage-tasks"><div v-for="task in stage.tasks" :key="task.id" class="plan-task"><time>{{ task.scheduledDate }}</time><span>{{ taskTypeLabels[task.taskType] || task.taskType }}</span><strong>{{ task.title }}</strong><el-tag v-if="task.status" :type="statusTypes[task.status] || 'info'">{{ statusLabels[task.status] || task.status }}</el-tag></div><el-empty v-if="!stage.tasks.length" :image-size="42" description="该阶段暂无计划事项" /></div>
        </div>
      </article></div>
    </section>
  </div>
</template>

<style scoped>
.plan-page{--plan-green:#237a43;--plan-ink:#25382f;--plan-muted:#718078}.plan-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding:8px 4px 24px;border-bottom:1px solid rgba(82,116,94,.18)}.hero-eyebrow,.section-title>div>span{color:#4c8d61;font-size:11px;font-weight:800;letter-spacing:1.6px}.plan-hero h1{margin-top:10px}.plan-hero p{margin:8px 0 0;color:var(--plan-muted)}.plan-overview{display:grid;grid-template-columns:1fr 1.25fr .55fr auto;align-items:center;margin:20px 0;padding:17px 20px;border:1px solid #dfe7dc;border-radius:10px;background:rgba(255,255,255,.76);box-shadow:0 7px 20px rgba(24,65,45,.045)}.plan-overview>div{min-width:0;padding:2px 20px;border-right:1px solid #e4e9e2}.plan-overview>div:first-child{padding-left:0}.plan-overview span,.plan-overview strong,.plan-overview small{display:block}.plan-overview span{color:#819087;font-size:11px}.plan-overview strong{overflow:hidden;margin:6px 0 4px;color:var(--plan-ink);font-size:17px;text-overflow:ellipsis;white-space:nowrap}.plan-overview small{color:#8d9992}.plan-overview .metric strong{color:var(--plan-green);font-size:25px}.plan-action{height:38px;margin-left:24px;padding:0 18px!important;border-color:#77a987!important;color:var(--plan-green)!important;background:transparent!important}.plan-action:hover,.plan-action:focus{border-color:var(--plan-green)!important;color:#185d34!important;background:transparent!important}.cycle-panel{padding:25px 28px;border:1px solid #dfe7dc;border-radius:10px;background:rgba(255,255,255,.74);box-shadow:0 7px 20px rgba(24,65,45,.045);backdrop-filter:blur(8px)}.section-title{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:22px}.section-title h2{margin:7px 0 4px;color:var(--plan-ink);font-size:22px}.section-title p{margin:0;color:var(--plan-muted)}.section-title em{padding:7px 11px;border-radius:8px;color:#47785a;background:#edf5eb;font-size:11px;font-style:normal}.stage-block{display:grid;grid-template-columns:42px minmax(0,1fr);gap:15px}.stage-rail{position:relative;display:flex;justify-content:center}.stage-rail::after{position:absolute;top:36px;bottom:-4px;width:1px;content:'';background:#d7e1d8}.stage-block:last-child .stage-rail::after{display:none}.stage-rail span{width:34px;height:34px;display:grid;place-items:center;z-index:1;border:1px solid #d3ded5;border-radius:50%;color:#6c8376;background:#faf9e8;font-weight:700}.stage-block.current .stage-rail span{color:#276e43;border-color:#82ae90;background:#e8f3e8;box-shadow:0 0 0 5px rgba(74,135,89,.08)}.stage-content{min-width:0;padding-bottom:12px}.stage-head{width:100%;min-height:64px;display:flex;align-items:flex-start;justify-content:space-between;gap:20px;padding:1px 8px 13px 0;border:0;border-radius:8px;color:inherit;background:transparent;text-align:left;cursor:pointer}.stage-head:hover{background:rgba(235,243,234,.58)}.stage-name{display:flex;align-items:center;gap:9px}.stage-name h3{margin:0;color:#2b3c33;font-size:17px}.stage-head p{margin:5px 0;color:#7d8d84}.stage-head small{color:#99a39d}.stage-date{display:flex;align-items:center;gap:8px;padding-top:3px;color:#718178;font-size:11px;white-space:nowrap}.stage-block.expanded .stage-date .el-icon{transform:rotate(180deg)}.stage-tasks{overflow:hidden;margin:0 0 12px;border:1px solid #e2e8df;border-radius:8px;background:rgba(255,255,255,.6)}.plan-task{display:grid;grid-template-columns:105px 120px minmax(210px,1fr) 78px;align-items:center;gap:12px;min-height:48px;padding:8px 13px;border-bottom:1px solid #e8ece6}.plan-task:last-child{border-bottom:0}.plan-task time{color:#72837a}.plan-task>span{color:#397c50}.plan-task strong{color:#36483f;font-weight:600}@media(max-width:900px){.plan-overview{grid-template-columns:1fr 1fr;gap:12px}.plan-overview>div{border:0;padding:8px 0}.plan-action{justify-self:start;margin-left:0}.plan-hero{align-items:flex-start;flex-direction:column}.plot-select{width:100%}.plan-task{grid-template-columns:95px 1fr auto}.plan-task>span{display:none}}@media(max-width:620px){.plan-overview{grid-template-columns:1fr}.cycle-panel{padding:20px 15px}.stage-head{flex-direction:column}.stage-date{padding:0}.plan-task{grid-template-columns:1fr auto}.plan-task strong{grid-column:1/-1}}
.stage-arrow{width:25px;height:25px;display:grid;place-items:center;border:1px solid rgba(111,135,121,.24);border-radius:50%;background:rgba(255,255,255,.62);transition:transform .2s ease,background-color .2s ease}.stage-block.expanded .stage-arrow{background:#edf5eb}
</style>
