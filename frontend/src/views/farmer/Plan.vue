<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { generateManagementPlan, getPlotTasks, previewManagementPlan } from '@/api/farmTask'
import { getCultivationTemplates, getPlotPlanting } from '@/api/cultivation'
import { useFarmerStore } from '@/stores/farmer'
import { FARM_TASK_TYPES, farmTaskTypeLabel } from '@/utils/farmTask'

const store = useFarmerStore()
const loading = ref(false)
const preview = ref(null)
const tasks = ref([])
const planting = ref(null)
const selectedTemplate = ref(null)
const expandedStages = ref(new Set())
const stageOptions = computed(() => selectedTemplate.value?.templateContent?.stages || [])
const activeTasks = computed(() => tasks.value.filter((task) => ['PENDING', 'OVERDUE'].includes(task.taskStatus)))
const stageLabels = computed(() => Object.fromEntries(stageOptions.value.map((stage) => [stage.code, stage.name])))
const statusLabels = { PENDING: '待执行', OVERDUE: '已逾期', COMPLETED: '已完成', CANCELLED: '已取消', SUPERSEDED: '已替代' }
const statusTypes = { PENDING: 'warning', OVERDUE: 'danger', COMPLETED: 'success', CANCELLED: 'info', SUPERSEDED: 'info' }
const periodLabels = { EARLY: '上旬', MID: '中旬', LATE: '下旬' }
const stageGlyphs = {
  SPRING_GROWTH: '芽',
  FLOWERING_FRUIT_SET: '花',
  YOUNG_FRUIT: '果',
  FRUIT_EXPANSION: '橙',
  MATURITY: '色',
  HARVEST_POSTHARVEST: '收',
  UNSET: '事',
}

const stageName = (code) => stageLabels.value[code] || code || '未设置阶段'
const currentStageCode = computed(() => planting.value?.currentStage?.stageCode)
const isStageExpanded = (code) => expandedStages.value.has(code)
function toggleStage(code) {
  const next = new Set(expandedStages.value)
  if (next.has(code)) next.delete(code)
  else next.add(code)
  expandedStages.value = next
}
function stageGlyph(group) {
  if (stageGlyphs[group.code]) return stageGlyphs[group.code]
  const name = stageName(group.code)
  const matched = name.match(/[\u4e00-\u9fa5]/)
  return matched?.[0] || '事'
}
const planGroups = computed(() => {
  const buckets = new Map()
  for (const task of tasks.value) {
    const code = task.stageCode || 'UNSET'
    if (!buckets.has(code)) buckets.set(code, [])
    buckets.get(code).push(task)
  }
  const order = [...stageOptions.value.map((stage) => stage.code), ...buckets.keys()]
  return [...new Set(order)].filter((code) => buckets.has(code)).map((code) => ({
    code,
    stage: stageOptions.value.find((item) => item.code === code),
    tasks: buckets.get(code).sort((a, b) => a.plannedDate.localeCompare(b.plannedDate)),
  }))
})

function stageWindow(stage) {
  if (!stage) return '日期待配置'
  const start = stage.start || { month: stage.startMonth, period: stage.startPeriod || 'EARLY' }
  const end = stage.end || { month: stage.endMonth, period: stage.endPeriod || 'LATE' }
  return `${start.month} 月${periodLabels[start.period] || ''}—${end.month} 月${periodLabels[end.period] || ''}`
}
function stageFocus(stage) {
  return Array.isArray(stage?.managementFocus) && stage.managementFocus.length ? stage.managementFocus.join(' · ') : '按模板落实阶段农事与巡园观察'
}
function changePreviewStage(row, code) {
  row.stageCode = code
  row.stageName = stageName(code)
}

async function loadTasks() {
  if (!store.selectedPlotId) return
  try { tasks.value = await getPlotTasks(store.selectedPlotId) }
  catch (error) { ElMessage.error(error.message || '计划任务加载失败') }
}
async function loadTemplateContext() {
  if (!store.selectedPlotId) return
  try {
    const [plantingResult, templates] = await Promise.all([getPlotPlanting(store.selectedPlotId), getCultivationTemplates()])
    planting.value = plantingResult
    selectedTemplate.value = templates.find((item) => item.templateId === plantingResult.templateId) || null
  } catch {
    planting.value = null
    selectedTemplate.value = null
  }
}
async function doPreview() {
  loading.value = true
  try { preview.value = await previewManagementPlan(store.selectedPlotId) }
  catch (error) { ElMessage.error(error.message || '计划预览失败') }
  finally { loading.value = false }
}
function exitPreview() { preview.value = null }
async function generate(regenerate = false) {
  if (regenerate) {
    try { await ElMessageBox.confirm('重新生成会将旧的未完成任务标记为已替代，已完成任务会保留。是否继续？', '重新生成管理计划', { type: 'warning' }) }
    catch { return }
  }
  loading.value = true
  try {
    const result = await generateManagementPlan(store.selectedPlotId, regenerate, preview.value?.tasks || null)
    ElMessage.success(`管理计划已生成，共 ${result.tasks.length} 项任务`)
    store.touchTimeline()
    await Promise.all([loadTasks(), loadTemplateContext()])
    preview.value = null
  } catch (error) { ElMessage.error(error.message || '计划生成失败') }
  finally { loading.value = false }
}

watch(() => store.selectedPlotId, () => {
  preview.value = null
  expandedStages.value = new Set()
  Promise.all([loadTasks(), loadTemplateContext()])
}, { immediate: true })
</script>

<template>
  <div class="farmer-page plan-page">
    <header class="plan-hero">
      <div><span class="hero-eyebrow">ORCHARD MANAGEMENT PLAN</span><h1 class="page-title">橙树全周期管理</h1><p>从萌芽、开花到成熟采收，将每个阶段的农事安排整理成清晰的生长档案。</p></div>
      <div class="hero-actions">
        <el-select :model-value="store.selectedPlotId" @change="store.selectPlot"><el-option v-for="plot in store.accessiblePlots" :key="plot.plotId" :label="plot.plotName" :value="plot.plotId" /></el-select>
        <el-button v-if="preview" @click="exitPreview">退出预览</el-button>
        <el-button v-else type="primary" plain :loading="loading" @click="doPreview">预览并调整计划</el-button>
      </div>
    </header>

    <section class="plan-overview">
      <div class="overview-item"><span>当前阶段</span><strong>{{ preview?.currentStage?.stageName || planting?.currentStage?.stageName || '暂无法判断' }}</strong><small>{{ planting?.currentStage?.stageSource === 'OVERRIDE' ? '现场人工修正' : '依据模板与当前日期计算' }}</small></div>
      <div class="overview-item"><span>品种模板</span><strong>{{ preview?.templateName || planting?.templateName || '尚未绑定模板' }}</strong><small>{{ selectedTemplate?.templateContent?.stageModelVersion || 'V1.1' }} · {{ selectedTemplate?.varietyName || planting?.varietyName || '-' }}</small></div>
      <div class="overview-item metric"><span>有效任务</span><strong>{{ activeTasks.length }}</strong><small>待执行与已逾期任务</small></div>
      <div class="overview-actions">
        <template v-if="preview"><el-button @click="exitPreview">取消调整</el-button><el-button v-if="!activeTasks.length" type="primary" @click="generate(false)">确认生成</el-button><el-button v-else type="warning" @click="generate(true)">确认重新生成</el-button></template>
        <el-button v-else type="primary" @click="doPreview" :loading="loading">{{ activeTasks.length ? '重新规划' : '生成管理计划' }}</el-button>
      </div>
    </section>

    <section v-if="preview" class="preview-panel" v-loading="loading">
      <div class="section-title"><div><span>PLAN PREVIEW</span><h2>计划预览与调整</h2><p>可以直接修改日期、阶段、农事类型和任务内容，确认后才会写入数据库。</p></div><em>共 {{ preview.tasks.length }} 项</em></div>
      <el-table :data="preview.tasks" max-height="560" class="preview-table">
        <el-table-column label="计划日期" width="155"><template #default="{ row }"><el-date-picker v-model="row.plannedDate" type="date" value-format="YYYY-MM-DD" size="small" /></template></el-table-column>
        <el-table-column label="生长阶段" min-width="180"><template #default="{ row }"><el-select :model-value="row.stageCode" size="small" @change="changePreviewStage(row, $event)"><el-option v-for="stage in stageOptions" :key="stage.code" :label="stage.name" :value="stage.code" /></el-select></template></el-table-column>
        <el-table-column label="农事类型" width="175"><template #default="{ row }"><el-select v-model="row.taskType" size="small" filterable><el-option v-for="item in FARM_TASK_TYPES" :key="item.value" :label="item.label" :value="item.value" /></el-select></template></el-table-column>
        <el-table-column label="任务内容" min-width="260"><template #default="{ row }"><el-input v-model="row.taskName" size="small" maxlength="100" /></template></el-table-column>
        <el-table-column label="操作" width="75"><template #default="{ $index }"><el-button link type="danger" :disabled="preview.tasks.length === 1" @click="preview.tasks.splice($index, 1)">移除</el-button></template></el-table-column>
      </el-table>
    </section>

    <section v-else class="cycle-panel" v-loading="loading">
      <div class="section-title"><div><span>FULL CYCLE ARCHIVE</span><h2>分阶段农事计划</h2><p>按生长阶段查看任务时间、内容与执行状态。</p></div><em>模板共 {{ stageOptions.length }} 个阶段</em></div>
      <el-empty v-if="!tasks.length" description="暂无已生成的计划，请先预览并确认生成" />
      <div v-else class="stage-list">
        <article v-for="group in planGroups" :key="group.code" class="stage-block" :class="{ current: group.code === currentStageCode, expanded: isStageExpanded(group.code) }">
          <div class="stage-rail"><span>{{ stageGlyph(group) }}</span></div>
          <div class="stage-content">
            <button class="stage-head" type="button" :aria-expanded="isStageExpanded(group.code)" @click="toggleStage(group.code)">
              <div class="stage-summary">
                <div class="stage-name-line"><h3>{{ stageName(group.code) }}</h3><el-tag v-if="group.code === currentStageCode" type="success" effect="light">当前阶段</el-tag></div>
                <p>{{ stageFocus(group.stage) }}</p>
                <small>{{ group.tasks.length }} 项农事安排</small>
              </div>
              <div class="stage-meta"><span>{{ stageWindow(group.stage) }}</span><el-icon class="stage-arrow"><ArrowDown /></el-icon></div>
            </button>
            <transition name="stage-expand">
              <div v-if="isStageExpanded(group.code)" class="task-list">
                <div v-for="task in group.tasks" :key="task.taskId" class="task-row">
                  <time>{{ task.plannedDate }}</time><span class="task-kind">{{ farmTaskTypeLabel(task.taskType) }}</span><strong>{{ task.taskName }}</strong><el-tag :type="statusTypes[task.taskStatus] || 'info'" effect="light">{{ statusLabels[task.taskStatus] || task.taskStatus }}</el-tag><small>{{ task.planBatchNo || '临时农事' }}</small>
                </div>
              </div>
            </transition>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.plan-page{--plan-green:#4f8066;--plan-ink:#40352e;--plan-muted:#819087}.plan-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding:12px 4px 28px;border-bottom:1px solid rgba(117,126,116,.2)}.hero-eyebrow,.section-title span{color:#8f765b;font-size:11px;font-weight:800;letter-spacing:1.6px}.plan-hero h1{margin-top:12px}.plan-hero p{margin:8px 0 0;color:var(--plan-muted);line-height:1.7}.hero-actions{display:flex;align-items:center;gap:10px}.hero-actions .el-select{width:240px}.plan-overview{display:grid;grid-template-columns:1fr 1.35fr .55fr auto;align-items:stretch;gap:0;margin:24px 0;padding:18px 20px;border:1px solid rgba(210,202,186,.8);border-radius:18px;background:rgba(255,254,249,.62);backdrop-filter:blur(9px);box-shadow:0 14px 34px rgba(66,64,48,.045)}.overview-item{min-width:0;padding:4px 22px;border-right:1px solid #e7e1d7}.overview-item:first-child{padding-left:4px}.overview-item span,.overview-item strong,.overview-item small{display:block}.overview-item span{color:#9a8878;font-size:11px}.overview-item strong{overflow:hidden;margin:7px 0 5px;color:var(--plan-ink);font-size:17px;text-overflow:ellipsis;white-space:nowrap}.overview-item small{color:#9aa29b}.overview-item.metric strong{color:var(--plan-green);font-size:25px}.overview-actions{display:flex;align-items:center;justify-content:flex-end;gap:9px;padding-left:22px}.cycle-panel,.preview-panel{padding:26px 28px 30px;border:1px solid rgba(210,202,186,.86);border-radius:21px;background:rgba(255,254,250,.7);backdrop-filter:blur(8px);box-shadow:0 14px 35px rgba(59,62,48,.045)}.section-title{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:24px}.section-title h2{margin:7px 0 4px;color:var(--plan-ink);font-size:22px}.section-title p{margin:0;color:var(--plan-muted)}.section-title em{padding:7px 11px;border-radius:10px;color:#587a68;background:#edf4ed;font-size:11px;font-style:normal}.stage-list{position:relative}.stage-block{display:grid;grid-template-columns:44px minmax(0,1fr);gap:16px;position:relative}.stage-rail{position:relative;display:flex;justify-content:center}.stage-rail::after{position:absolute;top:38px;bottom:-4px;width:1px;content:'';background:#d8ded7}.stage-block:last-child .stage-rail::after{display:none}.stage-rail span{width:36px;height:36px;display:grid;place-items:center;z-index:1;border:1px solid #d8ded7;border-radius:50%;color:#71867a;background:rgba(250,249,244,.84);font-family:"STKaiti","KaiTi",serif;font-size:16px;font-weight:700}.stage-block.current .stage-rail span{color:#376d51;border-color:#86ad94;background:#e9f3e9;box-shadow:0 0 0 6px rgba(96,148,111,.08)}.stage-content{min-width:0;padding:0 0 13px}.stage-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;width:100%;min-height:66px;margin:0;padding:2px 8px 14px 0;border:0;border-radius:12px;color:inherit;background:transparent;font:inherit;text-align:left;cursor:pointer;transition:background-color .2s ease}.stage-head:hover{background:rgba(237,244,237,.48)}.stage-head:focus-visible{outline:2px solid rgba(79,128,102,.38);outline-offset:2px}.stage-head h3{margin:0;color:#463a31;font-size:17px}.stage-head p{margin:6px 0 0;color:#8a958e;line-height:1.55}.stage-summary small{display:block;margin-top:7px;color:#aaa197;font-size:11px}.stage-name-line{display:flex;align-items:center;gap:9px}.stage-meta{display:flex;align-items:center;gap:12px;padding-top:3px;color:#9a8a79;font-size:11px;white-space:nowrap}.stage-arrow{width:25px;height:25px;border:1px solid rgba(128,145,134,.24);border-radius:50%;color:#6f8779;background:rgba(255,255,255,.58);font-size:13px;transition:transform .24s ease,background-color .2s ease}.stage-block.expanded .stage-arrow{transform:rotate(180deg);background:#edf4ed}.task-list{overflow:hidden;margin:0 0 14px;border:1px solid #ebe6dc;border-radius:13px;background:rgba(255,255,255,.48)}.task-row{display:grid;grid-template-columns:108px 150px minmax(230px,1fr) 80px 215px;align-items:center;gap:14px;min-height:50px;padding:8px 14px;border-bottom:1px solid #eeeae2;color:#6a6d68}.task-row:last-child{border-bottom:0}.task-row time{color:#8d7c6d;font-variant-numeric:tabular-nums}.task-row strong{color:#4a433c;font-weight:600}.task-row small{overflow:hidden;color:#a09a91;text-overflow:ellipsis;white-space:nowrap}.task-kind{color:#4e8066}.stage-expand-enter-active,.stage-expand-leave-active{transition:opacity .2s ease,transform .2s ease}.stage-expand-enter-from,.stage-expand-leave-to{opacity:0;transform:translateY(-5px)}.preview-table{--el-table-header-bg-color:#f6f5ef;--el-table-row-hover-bg-color:#f6faf4;border-radius:13px}.preview-table :deep(.el-date-editor){width:132px}.preview-table :deep(.el-select){width:100%}@media(max-width:1180px){.plan-overview{grid-template-columns:1fr 1fr}.overview-item:nth-child(2){border-right:0}.overview-item.metric{margin-top:14px}.overview-actions{margin-top:14px}.task-row{grid-template-columns:105px 140px minmax(180px,1fr) 80px}.task-row small{display:none}}@media(max-width:820px){.plan-hero,.stage-head{align-items:flex-start;flex-direction:column}.hero-actions,.hero-actions .el-select{width:100%}.plan-overview{grid-template-columns:1fr}.overview-item{padding:12px 4px;border-right:0;border-bottom:1px solid #e7e1d7}.overview-actions{justify-content:flex-start;padding:14px 4px 0}.cycle-panel,.preview-panel{padding:20px 16px}.stage-meta{justify-content:space-between;width:100%;padding-top:0}.task-row{grid-template-columns:1fr auto;gap:6px}.task-row strong{grid-column:1/-1}.task-kind{grid-row:1;grid-column:2}.task-row .el-tag{grid-column:2;grid-row:2}}
</style>
