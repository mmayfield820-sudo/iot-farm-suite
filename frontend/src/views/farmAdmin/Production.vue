<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { confirmFarmCleanupCompletion, confirmFarmHarvestCompletion, generateFarmPlans, getCropTemplateVersion, getFarmAnnualProduction, getFarmPlantingSchedule, getFarmProductionProfile, listCropTemplates, listFarmPlots, listFarms, saveFarmAnnualProduction, saveFarmPlantingSchedule, saveFarmProductionProfile, startFarmStage, updatePlotProductionOffset } from '@/api/production'
import { createHistoricalStageSupplement, createTaskChangeOrder, createTemporaryTask, listTasks } from '@/api/task'
import { usePlatformStore } from '@/stores/platform'

const platformStore = usePlatformStore()
const farms = ref([])
const templates = ref([])
const selectedFarmId = ref('')
const context = ref(null)
const plantingSchedule = ref(null)
const profile = ref(null)
const plots = ref([])
const currentStageTasks = ref([])
const loading = ref(false)
const generating = ref(false)
const saving = ref(false)
const setupOpen = ref(false)
const profileOpen = ref(false)
const milestoneOpen = ref(false)
const milestoneType = ref('harvest')
const dispatchOpen = ref(false)
const changeOrderOpen = ref(false)
const temporaryTaskOpen = ref(false)
const historicalSupplementOpen = ref(false)
const savingPlan = ref(false)
const planDirty = ref(false)
const planTemplateKey = ref('')
const planSourceVersionId = ref('')
const planTrack = ref('young')
const planStages = ref([])
const planChangeNote = ref('')
const form = reactive({ templateVersionId: '', plannedPlantingDate: '' })
const profileForm = reactive({ plantingDate: '', note: '' })
const milestoneForm = reactive({ completedAt: '' })
const dispatchForm = reactive({ stageCode: '', actualStartedAt: '', shiftFollowingStages: true })
const changeOrderForm = reactive({ taskId: '', scheduledDate: '', note: '', reason: '' })
const temporaryTaskForm = reactive({ plotId: '', taskType: '', title: '', scheduledDate: '', note: '', reason: '' })
const historicalSupplementForm = reactive({ stageCode: '', plotId: '', taskType: 'other', title: '', executedAt: '', executorName: '', result: '', note: '', reason: '' })
const savingPlotId = ref('')
const taskTypeOptions = [
  { value: 'inspection', label: '巡园检查' },
  { value: 'pruning', label: '修剪管理' },
  { value: 'fertilization', label: '施肥管理' },
  { value: 'flower_management', label: '花果管理' },
  { value: 'fruit_management', label: '果实管理' },
  { value: 'irrigation', label: '灌溉检查' },
  { value: 'pest_control', label: '病虫害防治' },
  { value: 'harvest', label: '采收管理' },
  { value: 'cleanup', label: '清园管理' },
  { value: 'other', label: '其他' },
]

const currentStageCode = computed(() => context.value?.stage?.code)
const lockedStageCodes = computed(() => new Set((context.value?.stages || []).filter((stage) => stage.locked).map((stage) => stage.code)))
const hasLockedStages = computed(() => lockedStageCodes.value.size > 0)
const dispatchableStages = computed(() => (context.value?.stages || []).filter((stage) => stage.status === 'active' || (stage.status === 'planned' && stage.canStart)))
const selectedDispatchStage = computed(() => dispatchableStages.value.find((stage) => stage.code === dispatchForm.stageCode))
const activeStage = computed(() => (context.value?.stages || []).find((stage) => stage.status === 'active'))
const historicalSupplementStage = computed(() => (context.value?.stages || []).find((stage) => stage.code === historicalSupplementForm.stageCode))
const adjustableTasks = computed(() => currentStageTasks.value.filter((task) => task.status === 'pending'))
const milestoneLabel = computed(() => milestoneType.value === 'harvest' ? '采收完成' : '清园完成')
const planTemplateOptions = computed(() => {
  const options = []
  if (context.value) options.push({ key: `current:${context.value.templateVersionId}:${context.value.track}`, versionId: context.value.templateVersionId, track: context.value.track, label: `当前已保存计划 · ${context.value.templateName} · ${context.value.track === 'young' ? '幼树版' : '成年树版'}` })
  for (const item of templates.value) {
    options.push({ key: `standard:${item.versionId}:young`, versionId: item.versionId, track: 'young', label: `${item.name} · 幼树版 · V${item.versionNo}` })
    options.push({ key: `standard:${item.versionId}:fruiting`, versionId: item.versionId, track: 'fruiting', label: `${item.name} · 成年树版 · V${item.versionNo}` })
  }
  return options
})
const planCurrentStage = computed(() => {
  const current = context.value?.stage
  if (!current) return null
  const scheduled = (context.value?.stages || []).find((stage) => stage.code === current.code)
  const edited = planStages.value.find((stage) => stage.code === current.code)
  return { ...current, ...scheduled, ...edited }
})
const planTrackLabel = computed(() => planTrack.value === 'young' ? '幼树轨道' : '结果树轨道')
const planTemplateSummary = computed(() => {
  const template = templates.value.find((item) => String(item.versionId) === String(planSourceVersionId.value))
  return {
    name: template?.name || context.value?.templateName || '尚未选择模板',
    versionNo: template?.versionNo || context.value?.versionNo,
  }
})
const selectedFarm = computed(() => farms.value.find((farm) => String(farm.id) === String(selectedFarmId.value)))

function dateRange(stage) { return `${stage.startsOn.slice(5).replace('-', '月')}日 - ${stage.endsOn.slice(5).replace('-', '月')}日` }
function rhythmDateRange(stage) { return `${stage.startsOn.slice(5).replace('-', '/')} ~ ${stage.endsOn.slice(5).replace('-', '/')}` }
function rhythmStatusLabel(status) { return status === 'planned' ? '未开始' : stageStatusLabel(status) }
function monthDayRange(stage) {
  if (!stage?.startsOn || !stage?.endsOn) return '尚无阶段日期'
  return `${stage.startsOn.slice(5).replace('-', '月')}日 ~ ${stage.endsOn.slice(5).replace('-', '月')}日`
}
function cloneDefinition(definition) { return JSON.parse(JSON.stringify(definition || { stages: [] })) }
function stageState(stage) { return (context.value?.stages || []).find((item) => item.code === stage.code) }
function stageLocked(stage) { return Boolean(stageState(stage)?.locked) }
function stageLockReason(stage) {
  const status = stageState(stage)?.status
  if (status === 'not_dispatched') return '该阶段已经过去且未下发，计划已归档锁定；如现场实际执行过工作，请使用补录。'
  if (status === 'active') return '该阶段已确认开始，计划已锁定；任务调整请使用变更单或临时任务。'
  if (status === 'completed') return '该阶段已经完成，计划作为生产档案锁定。'
  return ''
}
function stageStatusLabel(status) { return ({ planned: '待开始', active: '进行中', completed: '已完成', not_dispatched: '未下发' })[status] || status }
function stageStatusType(status) { return ({ planned: 'info', active: 'warning', completed: 'success', not_dispatched: 'info' })[status] || 'info' }
function hydratePlan() {
  if (!context.value) return
  planTemplateKey.value = `current:${context.value.templateVersionId}:${context.value.track}`
  planSourceVersionId.value = context.value.templateVersionId
  planTrack.value = context.value.track
  planStages.value = cloneDefinition(context.value.versionDefinition).stages
  planChangeNote.value = ''
  planDirty.value = false
}
async function loadContext() {
  context.value = null
  plantingSchedule.value = null
  profile.value = null
  plots.value = []
  currentStageTasks.value = []
  form.templateVersionId = ''
  form.plannedPlantingDate = ''
  if (!selectedFarmId.value) return
  try {
    context.value = await getFarmAnnualProduction(selectedFarmId.value)
    hydratePlan()
    form.templateVersionId = context.value.templateVersionId
    form.plannedPlantingDate = context.value.plantingDate
    const [profileResult, plotResult] = await Promise.allSettled([
      getFarmProductionProfile(selectedFarmId.value),
      listFarmPlots(selectedFarmId.value),
    ])
    if (profileResult.status === 'fulfilled') profile.value = profileResult.value
    else if (profileResult.reason.response?.status !== 404) throw profileResult.reason
    if (plotResult.status === 'fulfilled') plots.value = plotResult.value.items || []
    else throw plotResult.reason
    if (activeStage.value) {
      const taskRows = await listTasks({ scope: 'all', farmId: selectedFarmId.value })
      currentStageTasks.value = taskRows.filter((task) => task.stageCode === activeStage.value.code && ['pending', 'in_progress'].includes(task.status))
    }
  } catch (error) {
    if (![404, 409].includes(error.response?.status)) ElMessage.error(error.message || '年度生产资料加载失败')
    try {
      plantingSchedule.value = await getFarmPlantingSchedule(selectedFarmId.value)
      form.templateVersionId = plantingSchedule.value.templateVersionId || ''
      form.plannedPlantingDate = plantingSchedule.value.plannedPlantingDate || ''
    } catch (scheduleError) { ElMessage.error(scheduleError.message || '定植安排加载失败') }
  }
}
async function selectPlanTemplate(key) {
  const option = planTemplateOptions.value.find((item) => item.key === key)
  if (!option) return
  try {
    const detail = key.startsWith('current:') ? { versionDefinition: context.value.versionDefinition } : await getCropTemplateVersion(option.versionId)
    const incomingStages = cloneDefinition(detail.versionDefinition).stages
    const lockedStages = planStages.value.filter(stageLocked)
    const lockedByCode = new Map(lockedStages.map((stage) => [stage.code, stage]))
    const mergedStages = incomingStages.map((stage) => lockedByCode.get(stage.code) || stage)
    for (const stage of lockedStages) {
      if (!mergedStages.some((item) => item.code === stage.code)) mergedStages.splice(planStages.value.indexOf(stage), 0, stage)
    }
    planSourceVersionId.value = option.versionId
    if (!hasLockedStages.value) planTrack.value = option.track
    planStages.value = mergedStages
    planDirty.value = true
  } catch (error) { ElMessage.error(error.message || '标准模板内容加载失败') }
}
function addPlanTask(stage) { if (stageLocked(stage)) return; stage.tasks ||= []; stage.tasks.push({ type: 'other', title: '', offsetDays: 0, suggestedTime: null, note: '', track: null, repeatDays: null, repeatUntilStageEnd: false }); planDirty.value = true }
function removePlanTask(stage, index) { if (stageLocked(stage)) return; stage.tasks.splice(index, 1); planDirty.value = true }
function addPlanStage() { planStages.value.push({ code: `S${planStages.value.length + 1}`, name: '新生长阶段', durationDays: 30, moistureMin: 55, moistureMax: 70, managementFocus: '', tasks: [] }); planDirty.value = true }
function removePlanStage(index) { if (stageLocked(planStages.value[index])) return; planStages.value.splice(index, 1); planDirty.value = true }
function normalizePlanDefinition() {
  if (!planStages.value.length) throw new Error('管理计划至少需要一个生长阶段')
  return { stages: planStages.value.map((stage) => ({ ...stage, code: stage.code.trim(), name: stage.name.trim(), durationDays: Number(stage.durationDays), moistureMin: stage.moistureMin === null ? null : Number(stage.moistureMin), moistureMax: stage.moistureMax === null ? null : Number(stage.moistureMax), tasks: (stage.tasks || []).map((task) => ({ ...task, title: task.title.trim(), offsetDays: Number(task.offsetDays), repeatDays: task.repeatDays === null || task.repeatDays === '' ? null : Number(task.repeatDays), repeatUntilStageEnd: task.repeatDays !== null && task.repeatDays !== '' })) })) }
}
async function saveAnnualPlan() {
  try {
    const versionDefinition = normalizePlanDefinition()
    if (versionDefinition.stages.some((stage) => !stage.code || !stage.name || stage.durationDays <= 0 || (stage.moistureMin !== null && stage.moistureMax !== null && stage.moistureMin > stage.moistureMax))) return ElMessage.warning('请完整检查阶段名称、天数和土壤湿度范围')
    if (versionDefinition.stages.some((stage) => stage.tasks.some((task) => !task.title))) return ElMessage.warning('请填写所有任务名称')
    savingPlan.value = true
    context.value = await saveFarmAnnualProduction(selectedFarmId.value, { productionYear: context.value.productionYear, templateVersionId: planSourceVersionId.value, orchardTrack: planTrack.value, versionDefinition, changeNote: planChangeNote.value.trim() || null })
    hydratePlan()
    await loadContext()
    ElMessage.success('本农场年度管理计划已保存，确认无误后可下发任务')
  } catch (error) { ElMessage.error(error.message || '年度管理计划保存失败') }
  finally { savingPlan.value = false }
}
function openProfile() {
  profileForm.plantingDate = profile.value?.plantingDate || context.value?.plantingDate || ''
  profileForm.note = profile.value?.note || ''
  profileOpen.value = true
}
async function saveProfileSettings() {
  if (!profileForm.plantingDate) return ElMessage.warning('请填写实际定植日期')
  const planBasisChanged = profileForm.plantingDate !== context.value?.plantingDate
  saving.value = true
  try {
    await saveFarmProductionProfile(selectedFarmId.value, {
      templateVersionId: context.value.templateVersionId,
      plantingDate: profileForm.plantingDate,
      note: profileForm.note.trim() || null,
    })
    profileOpen.value = false
    await loadContext()
    ElMessage.success(planBasisChanged && context.value?.activePlanCount ? '计划依据已保存，请重新生成当前年度计划' : '管理计划已保存')
  } catch (error) { ElMessage.error(error.message || '管理计划保存失败') }
  finally { saving.value = false }
}
function openMilestone(type) {
  milestoneType.value = type
  const value = type === 'harvest' ? context.value?.harvestCompletedAt : context.value?.cleanupCompletedAt
  milestoneForm.completedAt = value?.slice(0, 19) || ''
  milestoneOpen.value = true
}
async function saveMilestone() {
  if (!milestoneForm.completedAt) return ElMessage.warning(`请选择${milestoneLabel.value}时间`)
  saving.value = true
  try {
    const api = milestoneType.value === 'harvest' ? confirmFarmHarvestCompletion : confirmFarmCleanupCompletion
    await api(selectedFarmId.value, { productionYear: context.value.productionYear, completedAt: milestoneForm.completedAt })
    milestoneOpen.value = false
    await loadContext()
    ElMessage.success(`${milestoneLabel.value}时间已记录`)
  } catch (error) { ElMessage.error(error.message || `${milestoneLabel.value}记录失败`) }
  finally { saving.value = false }
}
async function savePlotOffset(plot) {
  savingPlotId.value = plot.id
  try {
    const updated = await updatePlotProductionOffset(plot.id, { offsetDays: Number(plot.productionDateOffsetDays || 0) })
    Object.assign(plot, updated)
    ElMessage.success(`${plot.name}的日期偏移已保存`)
  } catch (error) { ElMessage.error(error.message || '地块日期偏移保存失败') }
  finally { savingPlotId.value = '' }
}
function openChangeOrder() {
  if (!activeStage.value) return ElMessage.warning('请先确认当前阶段并下发任务')
  if (!adjustableTasks.value.length) return ElMessage.warning('当前阶段没有可变更的待执行任务')
  const task = adjustableTasks.value[0]
  Object.assign(changeOrderForm, { taskId: task.id, scheduledDate: task.scheduledDate, note: task.note || '', reason: '' })
  changeOrderOpen.value = true
}
function selectChangeOrderTask(taskId) {
  const task = adjustableTasks.value.find((item) => item.id === taskId)
  if (task) Object.assign(changeOrderForm, { scheduledDate: task.scheduledDate, note: task.note || '' })
}
async function saveChangeOrder() {
  if (!changeOrderForm.taskId || !changeOrderForm.scheduledDate || !changeOrderForm.reason.trim()) return ElMessage.warning('请选择任务并填写变更原因')
  saving.value = true
  try {
    await createTaskChangeOrder(changeOrderForm.taskId, { scheduledDate: changeOrderForm.scheduledDate, note: changeOrderForm.note || null, reason: changeOrderForm.reason.trim() })
    changeOrderOpen.value = false
    await loadContext()
    ElMessage.success('变更单已生效，原任务和替代关系已保留')
  } catch (error) { ElMessage.error(error.message || '变更单保存失败') }
  finally { saving.value = false }
}
function openTemporaryTask() {
  if (!activeStage.value) return ElMessage.warning('请先确认当前阶段')
  Object.assign(temporaryTaskForm, { plotId: plots.value[0]?.id || '', taskType: '', title: '', scheduledDate: new Date().toISOString().slice(0, 10), note: '', reason: '' })
  temporaryTaskOpen.value = true
}
async function saveTemporaryTask() {
  if (!temporaryTaskForm.plotId || !temporaryTaskForm.taskType || !temporaryTaskForm.title.trim() || !temporaryTaskForm.scheduledDate || !temporaryTaskForm.reason.trim()) return ElMessage.warning('请完整填写地块、任务类型、任务名称、日期和新增原因')
  saving.value = true
  try {
    await createTemporaryTask(selectedFarmId.value, { ...temporaryTaskForm, title: temporaryTaskForm.title.trim(), taskType: temporaryTaskForm.taskType.trim(), note: temporaryTaskForm.note || null, reason: temporaryTaskForm.reason.trim() })
    temporaryTaskOpen.value = false
    await loadContext()
    ElMessage.success('临时任务已下发')
  } catch (error) { ElMessage.error(error.message || '临时任务下发失败') }
  finally { saving.value = false }
}
function openHistoricalSupplement(stage) {
  const state = stageState(stage)
  if (state?.status !== 'not_dispatched') return ElMessage.warning('只有已过去且未下发的阶段允许补录')
  Object.assign(historicalSupplementForm, {
    stageCode: stage.code,
    plotId: plots.value[0]?.id || '',
    taskType: 'other',
    title: '',
    executedAt: `${state.endsOn}T12:00:00`,
    executorName: '',
    result: '已完成',
    note: '',
    reason: '',
  })
  historicalSupplementOpen.value = true
}
async function saveHistoricalSupplement() {
  const formValue = historicalSupplementForm
  if (!formValue.plotId || !formValue.title.trim() || !formValue.executedAt || !formValue.executorName.trim() || !formValue.result.trim() || !formValue.reason.trim()) {
    return ElMessage.warning('请完整填写地块、工作内容、执行信息和补录原因')
  }
  saving.value = true
  try {
    await createHistoricalStageSupplement(selectedFarmId.value, formValue.stageCode, {
      productionYear: context.value.productionYear,
      plotId: formValue.plotId,
      taskType: formValue.taskType.trim(),
      title: formValue.title.trim(),
      executedAt: new Date(formValue.executedAt).toISOString(),
      executorName: formValue.executorName.trim(),
      result: formValue.result.trim(),
      note: formValue.note.trim() || null,
      reason: formValue.reason.trim(),
    })
    historicalSupplementOpen.value = false
    ElMessage.success('历史执行记录已补录，原阶段仍保持未下发和锁定状态')
  } catch (error) { ElMessage.error(error.message || '历史执行记录补录失败') }
  finally { saving.value = false }
}
async function loadResources() {
  loading.value = true
  try {
    const [farmRows, templateRows] = await Promise.all([listFarms(), listCropTemplates({ includeAllVersions: true })])
    farms.value = farmRows
    templates.value = templateRows
    selectedFarmId.value = farms.value.some((farm) => String(farm.id) === String(platformStore.selectedFarmId)) ? String(platformStore.selectedFarmId) : farms.value[0]?.id || ''
    if (selectedFarmId.value !== String(platformStore.selectedFarmId || '')) platformStore.selectFarm(selectedFarmId.value)
    await loadContext()
  } catch (error) { ElMessage.error(error.message || '农场资料加载失败') }
  finally { loading.value = false }
}
async function saveProfile() {
  if (!form.templateVersionId || !form.plannedPlantingDate) return ElMessage.warning('请选择标准模板并填写计划定植日期')
  saving.value = true
  try {
    await saveFarmPlantingSchedule(selectedFarmId.value, { templateVersionId: form.templateVersionId, plannedPlantingDate: form.plannedPlantingDate })
    setupOpen.value = false
    await loadContext()
    ElMessage.success('定植任务已下发；农户全部完成后将自动启用年度生产建议')
  } catch (error) { ElMessage.error(error.message || '生产资料保存失败') }
  finally { saving.value = false }
}
function openDispatch() {
  if (planDirty.value) return ElMessage.warning('当前管理计划有未保存修改，请先保存')
  if (!context.value?.annualConfigured) return ElMessage.warning('请先保存本农场年度管理计划')
  const defaultStage = dispatchableStages.value.find((stage) => stage.status === 'active') || dispatchableStages.value.find((stage) => stage.code === currentStageCode.value) || dispatchableStages.value[0]
  if (!defaultStage) return ElMessage.warning('当前没有可下发的阶段')
  dispatchForm.stageCode = defaultStage.code
  dispatchForm.actualStartedAt = defaultStage.actualStartedAt?.slice(0, 19) || ''
  dispatchForm.shiftFollowingStages = true
  dispatchOpen.value = true
}
async function generatePlans() {
  const stage = selectedDispatchStage.value
  if (!stage) return ElMessage.warning('请选择需要下发的阶段')
  if (stage.status !== 'active' && !dispatchForm.actualStartedAt) return ElMessage.warning('请确认该阶段的实际开始时间')
  try {
    await ElMessageBox.confirm(`将下发“${stage.name}”阶段任务。再次下发只替换该阶段尚未执行的任务，进行中和已完成任务保留。`, '确认阶段任务下发', { type: 'warning', confirmButtonText: '确认下发', cancelButtonText: '取消' })
    generating.value = true
    if (stage.status !== 'active') {
      await startFarmStage(selectedFarmId.value, { stageCode: stage.code, actualStartedAt: dispatchForm.actualStartedAt, shiftFollowingStages: dispatchForm.shiftFollowingStages })
    }
    const result = await generateFarmPlans(selectedFarmId.value, { stageCode: stage.code, regenerate: stage.dispatched || context.value.activePlanCount > 0 })
    dispatchOpen.value = false
    await loadContext()
    const skipped = result.skippedPlots || []
    if (skipped.length) ElMessage.warning(`已下发 ${result.taskCount} 项任务；未分配农户的地块已跳过：${skipped.map((plot) => plot.plotName).join('、')}`)
    else ElMessage.success(`${stage.name}阶段已下发，共 ${result.taskCount} 项待执行任务`)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      const detail = error.response?.data?.detail
      if (detail?.code === 'PLOT_ASSIGNEE_REQUIRED') {
        ElMessage.error(`请先为以下地块分配农户：${detail.plots.map((plot) => plot.plotName).join('、')}`)
      } else ElMessage.error(error.message || '生成失败')
    }
  } finally { generating.value = false }
}
onMounted(loadResources)
watch(() => platformStore.selectedFarmId, async (farmId) => {
  const id = String(farmId || '')
  if (!id || id === String(selectedFarmId.value) || !farms.value.some((farm) => String(farm.id) === id)) return
  selectedFarmId.value = id
  await loadContext()
})
</script>

<template>
  <div class="farmer-page annual-production-page">
    <div class="page-head">
      <div><h1 class="page-title">年度生产管理计划</h1><p class="page-subtitle">维护全年计划框架，并在物候阶段开始时滚动下发任务。</p></div>
      <div class="page-actions"><el-button @click="$router.push('/farm/cycle-draft')"><el-icon><DocumentAdd/></el-icon>创建下一年度管理计划</el-button><el-button type="primary" :loading="generating" :disabled="!context" @click="openDispatch"><el-icon><Promotion /></el-icon>下发任务</el-button></div>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else>
      <section class="farm-switcher"><div class="farm-display"><el-icon class="farm-display-icon"><House /></el-icon><strong>当前农场</strong><span>{{ selectedFarm?.name || '暂无可用农场' }}<template v-if="selectedFarm?.city"> · {{ selectedFarm.city }}</template></span></div><el-button v-if="!context" plain @click="setupOpen=true">安排定植</el-button><el-button v-else plain @click="openProfile">果园基础信息</el-button></section>
      <el-alert v-if="!context && !plantingSchedule?.plannedPlantingDate" title="尚未安排定植" description="选择标准模板和计划定植日期后，系统会向各有效地块下发定植任务。" type="warning" :closable="false" show-icon />
      <section v-else-if="!context" class="content-panel planting-wait"><div><span>计划定植日期</span><strong>{{ plantingSchedule.plannedPlantingDate }}</strong><p>{{ plantingSchedule.templateName }} · V{{ plantingSchedule.versionNo }}，仍有 {{ plantingSchedule.pendingTaskCount }} 个地块定植任务待完成。</p></div><el-button plain @click="setupOpen=true">调整安排</el-button></section>
      <template v-else>
        <el-alert v-if="context.overdueStages?.length" class="stage-overdue-alert" type="warning" :closable="false" show-icon :title="`有 ${context.overdueStages.length} 个阶段尚未确认开始`" :description="`请确认：${context.overdueStages.map((stage) => stage.name).join('、')}。未确认的阶段不会生成逾期任务。`" />
        <section class="milestone-grid">
          <article class="content-panel cycle-closeout"><div><span>采收完成时间</span><strong>{{ context?.harvestCompletedAt?.replace('T', ' ') || '尚未记录' }}</strong><small>作为生产档案留存，不触发生产年度切换。</small></div><el-button plain @click="openMilestone('harvest')">{{ context?.harvestCompletedAt ? '更新记录' : '记录采收完成' }}</el-button></article>
          <article class="content-panel cycle-closeout"><div><span>清园完成时间</span><strong>{{ context?.cleanupCompletedAt?.replace('T', ' ') || '尚未记录' }}</strong><small>作为验收、成本和追溯记录，不触发计划逻辑。</small></div><el-button plain @click="openMilestone('cleanup')">{{ context?.cleanupCompletedAt ? '更新记录' : '记录清园完成' }}</el-button></article>
        </section>
        <section class="content-panel plan-overview">
          <h3>年度计划基础信息</h3>
          <div class="plan-summary-grid">
            <article class="plan-summary-card">
              <header><span class="plan-summary-icon"><el-icon><Calendar /></el-icon></span><span>生产年度</span></header>
              <strong class="plan-summary-value">{{ context.productionYear }} 生产年度</strong>
              <small>{{ context.productionYearStartsOn }} ~ {{ context.productionYearEndsOn }}</small>
            </article>
            <article class="plan-summary-card">
              <header><span class="plan-summary-icon"><el-icon><Cherry /></el-icon></span><span>当前物候阶段</span></header>
              <strong class="plan-summary-value">{{ planCurrentStage?.name || '暂无匹配阶段' }}</strong>
              <small>{{ monthDayRange(planCurrentStage) }}</small>
            </article>
            <article class="plan-summary-card">
              <header><span class="plan-summary-icon"><el-icon><Orange /></el-icon></span><span>{{ planTrackLabel }}</span></header>
              <strong class="plan-summary-value">{{ context.treeAgeYears }} 年</strong>
              <small>全园统一轨道</small>
            </article>
            <article class="plan-summary-card">
              <header><span class="plan-summary-icon"><el-icon><Calendar /></el-icon></span><span>果园实际定植日期</span></header>
              <strong class="plan-summary-value">{{ context.plantingDate }}</strong>
              <small>农户完成全部定植任务后由系统确认</small>
            </article>
            <article class="plan-summary-card is-template">
              <header><span class="plan-summary-icon"><el-icon><Notebook /></el-icon></span><span>管理计划模板</span></header>
              <strong class="plan-summary-value">{{ planTemplateSummary.name }}<template v-if="planTemplateSummary.versionNo"> · V{{ planTemplateSummary.versionNo }}</template></strong>
              <small>{{ planDirty ? '当前计划有待保存调整' : context.templateScope === 'farm' ? '本农场已保存计划' : '公司级标准模板' }}</small>
            </article>
          </div>
        </section>
        <section class="content-panel phenology-overview">
          <header class="phenology-head">
            <div><h3>全年物候节奏</h3><p>默认上年 12 月至当年 11 月，阶段开始由农场管理员确认。</p></div>
            <div class="phenology-actions">
              <el-button :disabled="!activeStage || !adjustableTasks.length" @click="openChangeOrder"><el-icon><EditPen /></el-icon>新建变更单</el-button>
              <el-button type="primary" plain :disabled="!activeStage" @click="openTemporaryTask"><el-icon><Plus /></el-icon>新增临时任务</el-button>
            </div>
          </header>
          <div class="phenology-scroll">
            <div class="phenology-track">
              <article v-for="stage in context.stages" :key="stage.code" class="phenology-stage" :class="`is-${stage.status}`">
                <div class="phenology-marker"><span>{{ stage.code }}</span></div>
                <strong>{{ stage.name }}</strong>
                <small>{{ rhythmDateRange(stage) }}</small>
                <el-tag size="small" :type="stageStatusType(stage.status)" effect="plain">{{ rhythmStatusLabel(stage.status) }}</el-tag>
              </article>
            </div>
          </div>
        </section>
        <section class="management-editor content-panel" @input="planDirty=true" @change="planDirty=true">
          <header class="management-toolbar">
            <div><h3>本农场年度管理计划</h3><p>进行中、已完成和过去未下发的阶段均锁定；未下发阶段只允许补录实际执行记录。</p></div>
            <div class="plan-state"><el-tag :type="planDirty ? 'warning' : context.hasUndispatchedChanges ? 'info' : 'success'" effect="plain">{{ planDirty ? '有未保存修改' : context.hasUndispatchedChanges ? '已保存，待下发' : context.activePlanCount ? '已下发' : '尚未保存' }}</el-tag><el-button type="primary" :loading="savingPlan" @click.stop="saveAnnualPlan"><el-icon><DocumentChecked /></el-icon>保存管理计划</el-button></div>
          </header>
          <div class="plan-baseline">
            <el-form-item label="标准模板基线"><el-select v-model="planTemplateKey" filterable @change="selectPlanTemplate"><el-option v-for="item in planTemplateOptions" :key="item.key" :label="item.label" :value="item.key" :disabled="hasLockedStages && item.track !== planTrack"/></el-select></el-form-item>
            <el-form-item label="适用版本"><el-radio-group v-model="planTrack" :disabled="hasLockedStages"><el-radio-button value="young">幼树版</el-radio-button><el-radio-button value="fruiting">成年树版</el-radio-button></el-radio-group></el-form-item>
            <el-form-item label="本次调整说明"><el-input v-model="planChangeNote" placeholder="记录相对标准模板的调整内容" maxlength="500" show-word-limit/></el-form-item>
          </div>
          <div class="plan-stage-list">
            <article v-for="(stage, stageIndex) in planStages" :key="stage.code || stageIndex" class="plan-stage" :class="{ 'is-locked': stageLocked(stage) }">
              <header><div class="stage-heading"><strong>第 {{ stageIndex + 1 }} 阶段</strong><el-tag v-if="stageState(stage)" size="small" :type="stageStatusType(stageState(stage).status)" effect="plain">{{ stageStatusLabel(stageState(stage).status) }}</el-tag><el-icon v-if="stageLocked(stage)" class="stage-lock-icon" title="阶段已锁定"><Lock/></el-icon></div><div><el-button v-if="stageState(stage)?.status === 'not_dispatched'" link type="primary" @click="openHistoricalSupplement(stage)"><el-icon><DocumentAdd/></el-icon>补录实际执行</el-button><el-button link type="primary" :disabled="stageLocked(stage)" @click="addPlanTask(stage)"><el-icon><Plus/></el-icon>添加任务</el-button><el-button link type="danger" :disabled="planStages.length === 1 || stageLocked(stage)" @click="removePlanStage(stageIndex)"><el-icon><Delete/></el-icon>删除阶段</el-button></div></header>
              <p v-if="stageLockReason(stage)" class="stage-lock-note">{{ stageLockReason(stage) }}</p>
              <el-form class="plan-stage-fields" label-position="top"><el-form-item label="阶段编号"><el-input v-model="stage.code" :disabled="stageLocked(stage)"/></el-form-item><el-form-item label="阶段名称"><el-input v-model="stage.name" :disabled="stageLocked(stage)"/></el-form-item><el-form-item label="阶段天数"><el-input-number v-model="stage.durationDays" :min="1" :max="366" :disabled="stageLocked(stage)" controls-position="right"/></el-form-item><el-form-item label="土壤湿度下限（%）"><el-input-number v-model="stage.moistureMin" :min="0" :max="100" :disabled="stageLocked(stage)" controls-position="right"/></el-form-item><el-form-item label="土壤湿度上限（%）"><el-input-number v-model="stage.moistureMax" :min="0" :max="100" :disabled="stageLocked(stage)" controls-position="right"/></el-form-item><el-form-item label="管理重点"><el-input v-model="stage.managementFocus" :disabled="stageLocked(stage)"/></el-form-item></el-form>
              <div v-if="stage.tasks?.length" class="plan-task-columns"><span>适用版本</span><span>任务名称</span><span>阶段第几天</span><span>执行频次</span><span>执行说明</span><span></span></div>
              <div v-for="(task, taskIndex) in stage.tasks" :key="taskIndex" class="plan-task-row">
                <div class="plan-task-field"><span>适用版本</span><el-select v-model="task.track" :disabled="stageLocked(stage)"><el-option label="通用" :value="null"/><el-option label="幼树版" value="young"/><el-option label="成年树版" value="fruiting"/></el-select></div>
                <div class="plan-task-field"><span>任务名称</span><el-input v-model="task.title" placeholder="任务名称" :disabled="stageLocked(stage)"/></div>
                <div class="plan-task-field"><span>阶段第几天</span><el-input-number v-model="task.offsetDays" :min="0" :max="Math.max(0, stage.durationDays - 1)" :disabled="stageLocked(stage)" controls-position="right"/></div>
                <div class="plan-task-field"><span>执行频次</span><el-select v-model="task.repeatDays" :disabled="stageLocked(stage)"><el-option label="仅一次" :value="null"/><el-option label="每 7 天" :value="7"/><el-option label="每 14 天" :value="14"/><el-option label="每 30 天" :value="30"/></el-select></div>
                <div class="plan-task-field"><span>执行说明</span><el-input v-model="task.note" placeholder="执行说明" :disabled="stageLocked(stage)"/></div>
                <el-button circle text type="danger" title="删除任务" :disabled="stageLocked(stage)" @click="removePlanTask(stage, taskIndex)"><el-icon><Delete/></el-icon></el-button>
              </div>
              <el-empty v-if="!stage.tasks?.length" :image-size="40" description="本阶段暂无任务"/>
            </article>
          </div>
          <el-button class="add-plan-stage" plain type="primary" @click="addPlanStage"><el-icon><Plus/></el-icon>添加生长阶段</el-button>
        </section>
        <section class="annual-layout">
          <article class="content-panel suggestions"><div class="section-head"><div><h3>当前阶段建议</h3><p>任务由农场管理员按年度计划统一下发。</p></div></div><el-empty v-if="!context.suggestions.length" :image-size="52" description="当前阶段暂无建议"/><ul v-else><li v-for="item in context.suggestions" :key="`${item.title}-${item.scheduledDate}`"><span>{{ item.scheduledDate }}</span><div><strong>{{ item.title }}</strong><p>{{ item.note || '请结合现场树势、土壤湿度和天气安排。' }}</p></div></li></ul></article>
        </section>
      </template>
    </template>
    <el-dialog v-model="profileOpen" title="果园基础信息" width="min(900px, 94vw)">
      <el-form label-position="top">
        <div class="profile-fields"><el-form-item label="实际定植日期" required><el-date-picker v-model="profileForm.plantingDate" type="date" value-format="YYYY-MM-DD" :disabled-date="(day) => day > new Date()"/></el-form-item></div>
        <el-form-item label="果园备注"><el-input v-model="profileForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit/></el-form-item>
        <el-alert title="阶段和任务内容请直接在本页年度管理计划中修改并保存。" type="info" :closable="false" show-icon/>
      </el-form>
      <section class="profile-offsets">
        <div class="section-head"><div><h3>地块日期偏移</h3><p>在全园年度计划框架上，按地块物候提前或推迟任务日期。</p></div></div>
        <el-table :data="plots" size="small" empty-text="暂无地块">
          <el-table-column prop="name" label="地块" min-width="150"/>
          <el-table-column prop="farmerName" label="负责人" min-width="110"><template #default="{ row }">{{ row.farmerName || '未分配' }}</template></el-table-column>
          <el-table-column label="日期偏移（天）" min-width="290"><template #default="{ row }"><div class="offset-control"><el-input-number v-model="row.productionDateOffsetDays" :min="-60" :max="60" controls-position="right"/><small class="offset-help">负数提前，正数推迟</small></div></template></el-table-column>
          <el-table-column label="操作" width="80" align="right"><template #default="{ row }"><el-button link type="primary" :loading="savingPlotId === row.id" @click="savePlotOffset(row)">保存</el-button></template></el-table-column>
        </el-table>
      </section>
      <template #footer><el-button @click="profileOpen=false">取消</el-button><el-button type="primary" :loading="saving" @click="saveProfileSettings">保存基础信息</el-button></template>
    </el-dialog>
    <el-dialog v-model="milestoneOpen" :title="`记录${milestoneLabel}`" width="min(520px, 92vw)"><el-form label-position="top"><el-form-item :label="`${milestoneLabel}时间`" required><el-date-picker v-model="milestoneForm.completedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" format="YYYY年MM月DD日 HH:mm" placeholder="选择实际完成时间" :disabled-date="(day) => day > new Date()"/></el-form-item><el-alert title="该时间只进入生产档案，不影响管理计划的创建、保存、下发或年度切换。" type="info" :closable="false" show-icon/></el-form><template #footer><el-button @click="milestoneOpen=false">取消</el-button><el-button type="primary" :loading="saving" @click="saveMilestone">确认记录</el-button></template></el-dialog>
    <el-dialog v-model="dispatchOpen" title="按阶段下发任务" width="min(560px, 92vw)">
      <el-form label-position="top">
        <el-form-item label="目标阶段" required><el-select v-model="dispatchForm.stageCode" placeholder="选择要下发的阶段"><el-option v-for="stage in dispatchableStages" :key="stage.code" :label="`${stage.name} · ${stageStatusLabel(stage.status)} · ${dateRange(stage)}`" :value="stage.code"/></el-select></el-form-item>
        <template v-if="selectedDispatchStage?.status !== 'active'"><el-form-item label="实际开始时间" required><el-date-picker v-model="dispatchForm.actualStartedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" format="YYYY年MM月DD日 HH:mm" placeholder="确认现场物候阶段开始时间" :disabled-date="(day) => day > new Date()"/></el-form-item><el-checkbox v-model="dispatchForm.shiftFollowingStages">按实际开始时间整体偏移本阶段及后续阶段</el-checkbox></template>
        <el-alert class="dispatch-alert" title="下发后本阶段锁定；再次下发只替换尚未执行的任务，进行中和已完成任务保留。" type="info" :closable="false" show-icon/>
      </el-form>
      <template #footer><el-button @click="dispatchOpen=false">取消</el-button><el-button type="primary" :loading="generating" @click="generatePlans">确认下发</el-button></template>
    </el-dialog>
    <el-dialog v-model="changeOrderOpen" title="新建任务变更单" width="min(580px, 92vw)">
      <el-form label-position="top">
        <el-form-item label="原待执行任务" required><el-select v-model="changeOrderForm.taskId" filterable @change="selectChangeOrderTask"><el-option v-for="task in adjustableTasks" :key="task.id" :label="`${task.plotName} · ${task.title} · ${task.scheduledDate}`" :value="task.id"/></el-select></el-form-item>
        <el-form-item label="调整后日期" required><el-date-picker v-model="changeOrderForm.scheduledDate" type="date" value-format="YYYY-MM-DD" format="YYYY年MM月DD日" :disabled-date="(day) => day < new Date(new Date().setHours(0,0,0,0)) || (activeStage && day > new Date(`${activeStage.endsOn}T23:59:59`))"/></el-form-item>
        <el-form-item label="调整后执行说明"><el-input v-model="changeOrderForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit/></el-form-item>
        <el-form-item label="变更原因" required><el-input v-model="changeOrderForm.reason" type="textarea" :rows="2" maxlength="500" show-word-limit placeholder="例如：降雨导致喷药日期调整"/></el-form-item>
        <el-alert title="保存后原任务标记为已取消，新任务替代原任务；两条记录及变更原因均保留。" type="info" :closable="false" show-icon/>
      </el-form>
      <template #footer><el-button @click="changeOrderOpen=false">取消</el-button><el-button type="primary" :loading="saving" @click="saveChangeOrder">确认变更</el-button></template>
    </el-dialog>
    <el-dialog v-model="temporaryTaskOpen" title="新增当前阶段临时任务" width="min(580px, 92vw)">
      <el-form label-position="top">
        <el-form-item label="执行地块" required><el-select v-model="temporaryTaskForm.plotId" filterable><el-option v-for="plot in plots" :key="plot.id" :label="`${plot.name} · ${plot.farmerName || '未分配负责人'}`" :value="plot.id" :disabled="!plot.farmerUserId"/></el-select></el-form-item>
        <div class="temporary-task-fields"><el-form-item label="任务类型" required><el-select v-model="temporaryTaskForm.taskType" placeholder="请选择任务类型"><el-option v-for="item in taskTypeOptions" :key="item.value" :label="item.label" :value="item.value"/></el-select></el-form-item><el-form-item label="执行日期" required><el-date-picker v-model="temporaryTaskForm.scheduledDate" type="date" value-format="YYYY-MM-DD" format="YYYY年MM月DD日" :disabled-date="(day) => day < new Date(new Date().setHours(0,0,0,0)) || (activeStage && day > new Date(`${activeStage.endsOn}T23:59:59`))"/></el-form-item></div>
        <el-form-item label="任务名称" required><el-input v-model="temporaryTaskForm.title" maxlength="150"/></el-form-item>
        <el-form-item label="执行说明"><el-input v-model="temporaryTaskForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit/></el-form-item>
        <el-form-item label="新增原因" required><el-input v-model="temporaryTaskForm.reason" type="textarea" :rows="2" maxlength="500" show-word-limit placeholder="例如：突发病虫害，需要额外防治"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="temporaryTaskOpen=false">取消</el-button><el-button type="primary" :loading="saving" @click="saveTemporaryTask">下发临时任务</el-button></template>
    </el-dialog>
    <el-dialog v-model="historicalSupplementOpen" title="补录历史阶段实际执行" width="min(640px, 94vw)">
      <el-form label-position="top">
        <el-alert :title="`${historicalSupplementStage?.name || historicalSupplementForm.stageCode}为未下发历史阶段，补录不会重新下发任务或修改年度计划。`" type="warning" :closable="false" show-icon/>
        <div class="historical-fields">
          <el-form-item label="执行地块" required><el-select v-model="historicalSupplementForm.plotId" filterable><el-option v-for="plot in plots" :key="plot.id" :label="plot.name" :value="plot.id"/></el-select></el-form-item>
          <el-form-item label="任务类型" required><el-input v-model="historicalSupplementForm.taskType" maxlength="50"/></el-form-item>
          <el-form-item label="实际执行时间" required><el-date-picker v-model="historicalSupplementForm.executedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" format="YYYY年MM月DD日 HH:mm" :disabled-date="(day) => historicalSupplementStage && (day < new Date(`${historicalSupplementStage.startsOn}T00:00:00`) || day > new Date(`${historicalSupplementStage.endsOn}T23:59:59`))"/></el-form-item>
          <el-form-item label="实际执行人" required><el-input v-model="historicalSupplementForm.executorName" maxlength="50"/></el-form-item>
        </div>
        <el-form-item label="实际工作内容" required><el-input v-model="historicalSupplementForm.title" maxlength="150"/></el-form-item>
        <el-form-item label="执行结果" required><el-input v-model="historicalSupplementForm.result" maxlength="255"/></el-form-item>
        <el-form-item label="执行备注"><el-input v-model="historicalSupplementForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit/></el-form-item>
        <el-form-item label="补录原因" required><el-input v-model="historicalSupplementForm.reason" type="textarea" :rows="2" maxlength="500" show-word-limit placeholder="说明为何未在阶段内下发或及时记录"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="historicalSupplementOpen=false">取消</el-button><el-button type="primary" :loading="saving" @click="saveHistoricalSupplement">确认补录</el-button></template>
    </el-dialog>
    <el-dialog v-model="setupOpen" title="安排果园定植" width="min(520px, 92vw)"><el-form label-position="top"><el-form-item label="定植采用的标准模板" required><el-select v-model="form.templateVersionId" placeholder="选择脐橙标准模板"><el-option v-for="item in templates" :key="item.versionId" :label="`${item.name} · V${item.versionNo}`" :value="item.versionId"/></el-select></el-form-item><el-form-item label="计划定植日期" required><el-date-picker v-model="form.plannedPlantingDate" type="date" value-format="YYYY-MM-DD" :disabled-date="(day) => day < new Date(new Date().setHours(0, 0, 0, 0))"/><small class="field-help">保存后将为每个有效地块创建“完成脐橙定植”任务。农户全部完成后，系统以任务完成日期写入果园实际定植日期。</small></el-form-item></el-form><template #footer><el-button @click="setupOpen=false">取消</el-button><el-button type="primary" :loading="saving" @click="saveProfile">下发定植任务</el-button></template></el-dialog>
  </div>
</template>

<style scoped>
.farm-switcher{display:flex;align-items:center;gap:12px;margin-bottom:18px;padding:13px 16px;border:1px solid #cee6d8;border-radius:8px;background:#f8fcf9;color:#557164}.farm-switcher>span{color:#1f7a5b;font-size:12px;font-weight:700}.farm-switcher .el-select{width:300px}.profile-fields{display:grid;grid-template-columns:1fr;gap:12px}.profile-fields :deep(.el-date-editor){width:100%}.planting-wait,.cycle-closeout,.stage-adjustments{display:flex;align-items:center;justify-content:space-between;gap:18px}.planting-wait{margin-bottom:18px}.milestone-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}.planting-wait span,.planting-wait p,.cycle-closeout span,.cycle-closeout small,.stage-adjustments span,.stage-adjustments small{display:block;margin:0;color:#84938d;font-size:12px}.planting-wait strong,.cycle-closeout strong,.stage-adjustments strong{display:block;margin:6px 0;color:#315447;font-size:18px}.stage-adjustments{margin-bottom:18px}.stage-adjustments>div:last-child{display:flex;gap:10px}.plot-offsets{margin-bottom:18px}.offset-help{margin-left:8px;color:#84938d;font-size:11px}.dispatch-alert,.stage-overdue-alert{margin-bottom:18px}.dispatch-alert{margin-top:18px}.temporary-task-fields,.historical-fields{display:grid;grid-template-columns:1fr 1fr;gap:12px}.historical-fields{margin-top:16px}.field-help{color:#84938d;font-size:11px}.annual-layout{display:grid;grid-template-columns:1.25fr .75fr;gap:18px}.suggestions ul{display:grid;gap:2px;margin:0;padding:0;list-style:none}.suggestions li{display:grid;grid-template-columns:94px 1fr;gap:12px;padding:13px 0;border-bottom:1px solid #edf2ef}.suggestions li:last-child{border-bottom:0}.suggestions li>span{color:#b96d21;font-size:12px;font-weight:700}.suggestions li strong{color:#315447;font-size:14px}.suggestions li p{margin:5px 0 0;color:#70827b;font-size:12px;line-height:1.6}.timeline ol{display:grid;gap:4px;margin:0;padding:0;list-style:none}.timeline li{display:flex;gap:10px;padding:8px;color:#6f817a}.timeline li>span{width:28px;height:28px;display:grid;place-items:center;border:1px solid #dce9e3;border-radius:50%;font-size:10px}.timeline li div{display:grid;gap:2px}.timeline li strong{font-size:13px}.timeline li small{font-size:11px}.timeline li .el-tag{width:max-content;margin-top:3px}.timeline li.active{padding:10px;border-left:3px solid #e58226;color:#28533f;background:#fff8ef}.timeline li.active>span{border-color:#e58226;color:#bd6921}@media(max-width:760px){.annual-layout,.profile-fields,.milestone-grid,.temporary-task-fields,.historical-fields{grid-template-columns:1fr}.farm-switcher{align-items:stretch;flex-direction:column}.farm-switcher .el-select{width:100%}.planting-wait,.cycle-closeout,.stage-adjustments{align-items:flex-start;flex-direction:column}.stage-adjustments>div:last-child{width:100%;flex-wrap:wrap}}@media(max-width:440px){.suggestions li{grid-template-columns:1fr}}
.profile-offsets{margin-top:22px;padding-top:18px;border-top:1px solid #e5ece8}.profile-offsets .section-head{margin-bottom:12px}.profile-offsets .section-head h3,.profile-offsets .section-head p{margin:0}.profile-offsets .section-head h3{color:#315447;font-size:16px}.profile-offsets .section-head p{margin-top:5px;color:#7b8c85;font-size:12px}.offset-control{display:flex;align-items:center;gap:8px}.offset-control .offset-help{margin-left:0;white-space:nowrap}@media(max-width:560px){.offset-control{align-items:flex-start;flex-direction:column}}
.plan-overview{margin-bottom:18px;padding:22px}.plan-overview>h3{margin:0 0 18px;color:#284c3e;font-size:20px}.plan-summary-grid{display:grid;grid-template-columns:repeat(5,minmax(150px,1fr));gap:12px}.plan-summary-card{display:flex;min-width:0;min-height:210px;flex-direction:column;padding:20px;border:1px solid #edf2ef;border-radius:6px;background:#fcfefd}.plan-summary-card header{display:flex;min-height:48px;align-items:center;gap:10px;color:#567268;font-size:14px;font-weight:600}.plan-summary-icon{display:grid;width:44px;height:44px;flex:0 0 44px;place-items:center;border-radius:50%;background:#e9f8f0;color:#19845f}.plan-summary-icon .el-icon{font-size:23px}.plan-summary-value{display:block;margin:27px 0 16px;color:#174e3b;font-size:24px;line-height:1.35;overflow-wrap:anywhere}.plan-summary-card small{margin-top:auto;color:#7f918a;font-size:12px;line-height:1.65}.plan-summary-card.is-template .plan-summary-value{font-size:18px;line-height:1.55}@media(max-width:1400px){.plan-summary-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:900px){.plan-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){.plan-overview{padding:18px}.plan-summary-grid{grid-template-columns:1fr}.plan-summary-card{min-height:180px}.plan-summary-value{margin-top:22px}}
.phenology-overview{margin-bottom:18px;padding:22px}.phenology-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}.phenology-head h3,.phenology-head p{margin:0}.phenology-head h3{color:#284c3e;font-size:20px}.phenology-head p{margin-top:8px;color:#788a83;font-size:13px}.phenology-actions{display:flex;flex:0 0 auto;gap:10px}.phenology-scroll{margin-top:34px;overflow-x:auto;padding-bottom:5px}.phenology-track{display:flex;min-width:max-content}.phenology-stage{position:relative;display:flex;width:150px;min-height:185px;flex:1 0 150px;align-items:center;flex-direction:column;text-align:center}.phenology-stage::before{content:"";position:absolute;top:27px;right:0;left:0;height:2px;background:#d9e2de}.phenology-stage:first-child::before{left:50%}.phenology-stage:last-child::before{right:50%}.phenology-marker{position:relative;z-index:1;display:grid;width:56px;height:56px;place-items:center;border:2px solid #d9e2de;border-radius:50%;background:#f7f9f8;color:#52645d}.phenology-marker span{font-size:15px}.phenology-stage.is-completed::before,.phenology-stage.is-not_dispatched::before{background:#28a979}.phenology-stage.is-active::before{background:#ed7b0a}.phenology-stage.is-completed .phenology-marker,.phenology-stage.is-not_dispatched .phenology-marker{border-color:#28a979;background:#28a979;color:#fff}.phenology-stage.is-active .phenology-marker{border-color:#ed7b0a;background:#ed7b0a;color:#fff}.phenology-stage>strong{min-height:42px;margin:18px 8px 4px;color:#315447;font-size:15px;line-height:1.45}.phenology-stage.is-active>strong{color:#c96914}.phenology-stage>small{min-height:28px;color:#687b73;font-size:12px}.phenology-stage>.el-tag{margin-top:9px;border:0;border-radius:12px}.annual-layout{display:block}@media(max-width:760px){.phenology-head{flex-direction:column}.phenology-actions{width:100%;flex-wrap:wrap}.phenology-scroll{margin-top:26px}}@media(max-width:440px){.phenology-actions .el-button{flex:1;margin:0}.phenology-stage{width:132px;flex-basis:132px}}
.management-editor{margin-bottom:18px;background:#fff}.management-toolbar{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:0 0 18px}.management-toolbar h3,.management-toolbar p{margin:0}.management-toolbar h3{color:#315447;font-size:18px}.management-toolbar p{margin-top:5px;color:#7b8c85;font-size:12px}.plan-state{display:flex;align-items:center;gap:10px}.plan-baseline{display:grid;grid-template-columns:minmax(280px,1.2fr) auto minmax(260px,1fr);gap:12px;padding:14px 0;border-top:1px solid #edf2ef}.plan-baseline :deep(.el-form-item){margin-bottom:0}.plan-baseline :deep(.el-select){width:100%}.plan-stage-list{display:grid;border-top:1px solid #edf2ef}.plan-stage{padding:17px 0;border-bottom:1px solid #edf2ef}.plan-stage.is-locked{background:#fafcfb}.plan-stage>header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}.plan-stage>header strong{color:#315447}.plan-stage>header>div{display:flex;gap:6px}.stage-heading{align-items:center}.stage-lock-icon{color:#84938d}.stage-lock-note{margin:-3px 0 12px;padding:8px 10px;border-left:3px solid #c8d8d0;color:#687b73;background:#f4f8f6;font-size:12px;line-height:1.55}.plan-stage-fields{display:grid;grid-template-columns:minmax(84px,.45fr) minmax(180px,1.1fr) minmax(110px,.55fr) minmax(130px,.7fr) minmax(130px,.7fr) minmax(210px,1.3fr);gap:10px}.plan-stage-fields :deep(.el-form-item){min-width:0;margin-bottom:10px}.plan-stage-fields :deep(.el-form-item__label){height:auto;min-height:20px;padding:0 0 5px;line-height:1.35}.plan-stage-fields :deep(.el-input-number),.plan-task-field :deep(.el-input-number),.plan-task-field :deep(.el-select){width:100%}.plan-task-columns,.plan-task-row{display:grid;grid-template-columns:110px minmax(150px,1fr) 110px 120px minmax(180px,1.3fr) 32px;gap:10px}.plan-task-columns{padding:0 2px;color:#829089;font-size:11px}.plan-task-row{align-items:end;margin-top:8px}.plan-task-field{display:grid;min-width:0}.plan-task-field>span{display:none;color:#71827b;font-size:11px;line-height:1.35}.add-plan-stage{width:100%;margin:14px 0 0}@media(max-width:1500px){.plan-baseline{grid-template-columns:1fr 1fr}.plan-baseline .el-form-item:last-child{grid-column:1/-1}.plan-stage-fields{grid-template-columns:repeat(3,minmax(0,1fr))}.plan-task-columns{display:none}.plan-task-row{grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:12px;border:1px solid #edf2ef;border-radius:8px;background:#fcfefd}.plan-task-field{gap:5px}.plan-task-field>span{display:block}.plan-task-row>.el-button{justify-self:end}}@media(max-width:760px){.management-toolbar{align-items:flex-start;flex-direction:column}.plan-state{width:100%;justify-content:space-between}.plan-baseline,.plan-stage-fields,.plan-task-row{grid-template-columns:1fr}.plan-baseline .el-form-item:last-child{grid-column:auto}.plan-stage>header{align-items:flex-start;flex-direction:column}.plan-task-row>.el-button{margin-top:2px}}
.farm-switcher{min-height:58px;justify-content:space-between;padding:13px 18px;border-color:#dfe7e3;background:#fff}
.farm-display{display:flex;min-width:0;align-items:center;gap:13px}
.farm-display-icon{flex:0 0 auto;color:#18835c;font-size:24px}
.farm-display strong{flex:0 0 auto;color:#263e36;font-size:14px}
.farm-display>span:last-child{overflow:hidden;color:#4f675e;font-size:14px;text-overflow:ellipsis;white-space:nowrap}
@media(max-width:760px){.farm-display{width:100%;gap:10px}.farm-display>span:last-child{white-space:normal}.farm-switcher>.el-button{align-self:flex-start}}
</style>
