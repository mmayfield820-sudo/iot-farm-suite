<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { generateManagementPlan, getPlotTasks, previewManagementPlan } from '@/api/farmTask'
import { getCultivationTemplates, getPlotPlanting } from '@/api/cultivation'
import { useFarmerStore } from '@/stores/farmer'

const store = useFarmerStore()
const loading = ref(false)
const preview = ref(null)
const tasks = ref([])
const stageOptions = ref([])
const activeTasks = computed(() => tasks.value.filter((task) => ['PENDING', 'OVERDUE'].includes(task.taskStatus)))
const stageLabels = computed(() => Object.fromEntries(stageOptions.value.map((stage) => [stage.code, stage.name])))
const statusLabels = { PENDING: '待执行', OVERDUE: '已逾期', COMPLETED: '已完成', CANCELLED: '已取消', SUPERSEDED: '已替代' }
const statusTypes = { PENDING: 'warning', OVERDUE: 'danger', COMPLETED: 'success', CANCELLED: 'info', SUPERSEDED: 'info' }
const taskTypeOptions = [
  { value: 'PATROL', label: '巡园检查' },
  { value: 'IRRIGATION', label: '灌溉' },
  { value: 'FERTILIZATION', label: '施肥' },
  { value: 'PRUNING', label: '整形修剪' },
  { value: 'PEST_CONTROL', label: '病虫害防治' },
  { value: 'WEEDING', label: '除草' },
  { value: 'HARVEST', label: '采收' },
]

const taskTypeLabel = (value) => taskTypeOptions.find((item) => item.value === value)?.label || value || '其他农事'
const stageName = (code) => stageLabels.value[code] || code || '未设置阶段'

function changePreviewStage(row, code) {
  row.stageCode = code
  row.stageName = stageName(code)
}

async function loadTasks() {
  if (!store.selectedPlotId) return
  try { tasks.value = await getPlotTasks(store.selectedPlotId) }
  catch (error) { ElMessage.error(error.message || '计划任务加载失败') }
}
async function loadStageOptions() {
  if (!store.selectedPlotId) return
  try {
    const [planting, templates] = await Promise.all([getPlotPlanting(store.selectedPlotId), getCultivationTemplates()])
    const template = templates.find((item) => item.templateId === planting.templateId)
    stageOptions.value = template?.templateContent?.stages || []
  } catch { stageOptions.value = [] }
}
async function doPreview() {
  loading.value = true
  try { preview.value = await previewManagementPlan(store.selectedPlotId) }
  catch (error) { ElMessage.error(error.message || '计划预览失败') }
  finally { loading.value = false }
}
function exitPreview() {
  preview.value = null
}
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
    await loadTasks()
    preview.value = null
  } catch (error) { ElMessage.error(error.message || '计划生成失败') }
  finally { loading.value = false }
}
watch(() => store.selectedPlotId, () => {
  preview.value = null
  Promise.all([loadTasks(), loadStageOptions()])
}, { immediate: true })
</script>

<template>
  <div class="farmer-page plan-page">
    <div class="page-head"><div><h1 class="page-title">管理计划</h1><p class="page-subtitle">根据地块模板、种植信息和当前阶段生成未来农事任务。</p></div><el-select :model-value="store.selectedPlotId" @change="store.selectPlot" style="width:260px"><el-option v-for="plot in store.accessiblePlots" :key="plot.plotId" :label="plot.plotName" :value="plot.plotId" /></el-select></div>
    <el-card shadow="never" class="summary-card">
      <div class="summary-head"><div><span>当前有效任务</span><strong>{{ activeTasks.length }}</strong></div><div v-if="preview"><span>当前阶段</span><strong>{{ preview.currentStage.stageName }}</strong></div><div v-if="preview"><span>模板</span><strong>{{ preview.templateName }} · V{{ preview.templateVersion }}</strong></div><div class="actions"><el-button v-if="preview" @click="exitPreview">退出预览</el-button><el-button v-else @click="doPreview" :loading="loading">预览管理计划</el-button><el-button v-if="!activeTasks.length" type="primary" @click="generate(false)" :disabled="!preview">确认生成</el-button><el-button v-else type="warning" @click="generate(true)" :disabled="!preview">重新生成</el-button></div></div>
      <el-alert v-if="preview" :title="`当前预览包含 ${preview.tasks.length} 项任务，可直接修改日期、阶段、类型和任务内容后生成。`" type="info" :closable="false" show-icon />
    </el-card>
    <el-card v-if="preview" shadow="never" class="task-card">
      <template #header><div class="preview-head"><b>计划预览与调整</b><div><span>修改仅在确认生成后写入数据库</span><el-button link type="primary" @click="exitPreview">退出预览</el-button></div></div></template>
      <el-table :data="preview.tasks" max-height="520">
        <el-table-column label="计划日期" width="155"><template #default="{ row }"><el-date-picker v-model="row.plannedDate" type="date" value-format="YYYY-MM-DD" size="small" /></template></el-table-column>
        <el-table-column label="生长阶段" min-width="180"><template #default="{ row }"><el-select :model-value="row.stageCode" size="small" @change="changePreviewStage(row, $event)"><el-option v-for="stage in stageOptions" :key="stage.code" :label="stage.name" :value="stage.code" /></el-select></template></el-table-column>
        <el-table-column label="农事类型" width="155"><template #default="{ row }"><el-select v-model="row.taskType" size="small" filterable><el-option v-for="item in taskTypeOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></template></el-table-column>
        <el-table-column label="任务内容" min-width="240"><template #default="{ row }"><el-input v-model="row.taskName" size="small" maxlength="100" /></template></el-table-column>
        <el-table-column label="操作" width="75"><template #default="{ $index }"><el-button link type="danger" :disabled="preview.tasks.length === 1" @click="preview.tasks.splice($index, 1)">移除</el-button></template></el-table-column>
      </el-table>
    </el-card>
    <el-card v-else shadow="never" class="task-card"><template #header><b>当前计划任务</b></template><el-table :data="tasks"><el-table-column prop="plannedDate" label="计划日期" width="130" /><el-table-column label="阶段" min-width="160"><template #default="{ row }">{{ stageName(row.stageCode) }}</template></el-table-column><el-table-column prop="taskName" label="任务" min-width="220" /><el-table-column label="状态" width="120"><template #default="{ row }"><el-tag :type="statusTypes[row.taskStatus] || 'info'">{{ statusLabels[row.taskStatus] || row.taskStatus }}</el-tag></template></el-table-column><el-table-column prop="planBatchNo" label="计划批次" min-width="220" /></el-table></el-card>
  </div>
</template>

<style scoped>
.page-head,.summary-head{display:flex;justify-content:space-between;gap:18px;align-items:center}.summary-card,.task-card{margin-bottom:20px;border-color:#ecd8c8}.summary-head>div{display:flex;flex-direction:column;gap:5px}.summary-head span{font-size:13px;color:#99725a}.summary-head strong{color:#4a2816}.summary-head .actions{margin-left:auto;display:flex;flex-direction:row;align-items:center}.preview-head,.preview-head>div{display:flex;align-items:center;justify-content:space-between;gap:16px}.preview-head span{color:#a18472;font-size:11px}.task-card :deep(.el-date-editor){width:132px}.task-card :deep(.el-select){width:100%}@media(max-width:900px){.summary-head{align-items:flex-start;flex-direction:column}.summary-head .actions{margin-left:0}.preview-head{align-items:flex-start;flex-direction:column}}
</style>
