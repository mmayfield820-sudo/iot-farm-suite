<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createAdHocTask, completeTask, correctTaskCompletion, getTask, listTasks } from '@/api/task'
import { getPlotProductionContext } from '@/api/production'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'
import { formatDateTime as formatLocalDateTime } from '@/utils/dataAdapters'
import PlotOverviewIcon from '@/components/PlotOverviewIcon.vue'
import TaskSummaryIcon from '@/components/TaskSummaryIcon.vue'

const farmerStore = useFarmerStore()
const userStore = useUserStore()
const scopes = [
  { key: 'today', label: '今日' },
  { key: 'overdue', label: '逾期' },
  { key: 'next7days', label: '未来 7 天' },
  { key: 'month', label: '月历' },
]
const activeScope = ref('today')
const loading = ref(false)
const tasks = ref([])
const detail = ref(null)
const detailLoading = ref(false)
const productionContext = ref(null)
const productionContextError = ref('')
const headerProductionContext = ref(null)
const drawerOpen = ref(false)
const completionOpen = ref(false)
const correctionOpen = ref(false)
const adHocOpen = ref(false)
const submitting = ref(false)
const localNow = new Date()
const localMonth = `${localNow.getFullYear()}-${String(localNow.getMonth() + 1).padStart(2, '0')}`
const filters = reactive({ plotId: farmerStore.selectedPlotId || '', status: '', month: localMonth })
const calendarDate = ref(new Date(`${filters.month}-01T00:00:00`))
const completionForm = reactive({ result: '已完成', executedAt: '', executorName: '', note: '' })
const correctionForm = reactive({ result: '', executedAt: '', executorName: '', note: '', reason: '' })
const adHocForm = reactive({ plotId: '', taskType: '巡园', title: '', executedAt: '', executorName: '', note: '' })

const visibleTasks = computed(() => tasks.value)
const calendarTitle = computed(() => `${calendarDate.value.getFullYear()} 年 ${calendarDate.value.getMonth() + 1} 月`)
const tasksByDate = computed(() => tasks.value.reduce((result, task) => {
  const key = taskCalendarKey(task)
  if (!key) return result
  if (!result[key]) result[key] = []
  result[key].push(task)
  return result
}, {}))
const taskCounts = computed(() => ({
  pending: tasks.value.filter((item) => item.status === 'pending').length,
  inProgress: tasks.value.filter((item) => item.status === 'in_progress').length,
  overdue: tasks.value.filter((item) => item.status === 'overdue').length,
  completed: tasks.value.filter((item) => item.status === 'completed').length,
}))
const plotOptions = computed(() => farmerStore.farmPlots || [])
const canExecute = computed(() => detail.value && !['completed', 'cancelled'].includes(detail.value.status))
const headerPlotId = computed(() => filters.plotId || farmerStore.currentPlot?.plotId || plotOptions.value[0]?.plotId)
const managementStage = computed(() => headerProductionContext.value?.stage)
const managementStageName = computed(() => {
  if (managementStage.value) return `${managementStage.value.name}${managementStage.value.code ? `（${managementStage.value.code}）` : ''}`
  const fallback = farmerStore.currentPlot?.cropStage || '暂无阶段信息'
  const parts = String(fallback).split(/·/).map((item) => item.trim())
  return parts.length === 2 ? `${parts[1]}（${parts[0]}）` : fallback
})
const managementStagePeriod = computed(() => {
  const stage = managementStage.value
  if (!stage?.startsOn || !stage?.endsOn) return ''
  const startMonth = Number(String(stage.startsOn).slice(5, 7))
  const endMonth = Number(String(stage.endsOn).slice(5, 7))
  return startMonth === endMonth ? `${startMonth}月` : `${startMonth}月 - ${endMonth}月`
})

function statusLabel(status) {
  return ({ pending: '待处理', in_progress: '进行中', completed: '已完成', overdue: '已逾期', cancelled: '已取消' })[status] || status
}
function statusTone(status) {
  return ({ overdue: 'danger', cancelled: 'info', in_progress: 'warning', completed: 'success', pending: 'neutral' })[status] || 'neutral'
}
function sourceLabel(source) { return source === 'ad_hoc' ? '现场补录' : source === 'temporary' ? '临时任务' : source === 'planting' ? '定植任务' : '计划任务' }
function taskFarmName(task) { return farmerStore.getPlot(task.plotId)?.farmName || '未命名农场' }
function taskStageLabel(task) {
  if (task.plotId === headerPlotId.value && managementStage.value?.code === task.stageCode) {
    return `${managementStage.value.name}（${task.stageCode}）`
  }
  return task.stageCode ? `管理阶段：${task.stageCode}` : '现场农事'
}
function formatDate(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('zh-CN', { month: 'short', day: 'numeric', weekday: 'short' }).format(new Date(`${value}T00:00:00`))
}
function formatDateTime(value) {
  return formatLocalDateTime(value, '-')
}
function asInputDateTime(value = new Date()) {
  const date = typeof value === 'string' ? new Date(value) : value
  const offset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}
function asUtc(value) { return new Date(value).toISOString() }
function isActionable(task) { return !['completed', 'cancelled'].includes(task.status) }
function dateKey(date) {
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}
function taskCalendarKey(task) {
  const raw = task.scheduledDate ?? task.scheduled_date ?? task.plannedDate ?? task.planned_date ?? task.date
  if (!raw) return ''
  if (raw instanceof Date) return dateKey(raw)
  const value = String(raw).trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value
  const parsed = new Date(value)
  if (!Number.isNaN(parsed.getTime())) return dateKey(parsed)
  return value.match(/^\d{4}-\d{2}-\d{2}/)?.[0] || ''
}
function dayTasks(day) { return tasksByDate.value[day] || [] }
function calendarTaskTitle(task) { return filters.plotId ? task.title : `${task.plotName || '未命名地块'} · ${task.title}` }
function isToday(day) { return day === dateKey(new Date()) }
function calendarTaskTone(task) {
  if (task.status === 'overdue') return 'rose'
  if (task.status === 'completed') return 'muted'
  const type = String(task.taskType || '')
  if (/灌溉|浇水|irrigation/i.test(type)) return 'blue'
  if (/施肥|除草|清园|fertil/i.test(type)) return 'green'
  if (/修剪|prun/i.test(type)) return 'purple'
  return 'orange'
}
function changeCalendarMonth(offset) {
  const current = calendarDate.value
  calendarDate.value = new Date(current.getFullYear(), current.getMonth() + offset, 1)
}
function goCalendarToday() { calendarDate.value = new Date() }
async function changeCalendarFilter(value) {
  if (value) calendarDate.value = new Date(`${value}-01T00:00:00`)
  await loadTasks()
}

async function loadTasks() {
  loading.value = true
  try {
    const params = { scope: activeScope.value, farmId: farmerStore.currentFarm?.farmId }
    if (filters.plotId) params.plotId = filters.plotId
    if (filters.status) params.status = filters.status
    if (activeScope.value === 'month') params.month = filters.month
    tasks.value = await listTasks(params)
  } catch (error) {
    ElMessage.error(error.message || '农事任务加载失败')
  } finally {
    loading.value = false
  }
}

async function loadHeaderProductionContext(plotId) {
  headerProductionContext.value = null
  if (!plotId) return
  try {
    headerProductionContext.value = await getPlotProductionContext(plotId)
  } catch {
    headerProductionContext.value = null
  }
}

async function changeScope(scope) {
  activeScope.value = scope
  await loadTasks()
}
async function openTask(task) {
  detailLoading.value = true
  drawerOpen.value = true
  productionContext.value = null
  productionContextError.value = ''
  try {
    detail.value = await getTask(task.id)
    if (detail.value.source !== 'ad_hoc') {
      try {
        productionContext.value = await getPlotProductionContext(detail.value.plotId)
      } catch (error) {
        productionContextError.value = error.message || '暂未取得生产周期资料'
      }
    }
  } catch (error) {
    drawerOpen.value = false
    ElMessage.error(error.message || '任务详情加载失败')
  } finally {
    detailLoading.value = false
  }
}
function closeDrawer() { drawerOpen.value = false; detail.value = null; productionContext.value = null; productionContextError.value = '' }
function openCompletion() {
  completionForm.result = '已完成'
  completionForm.executedAt = asInputDateTime()
  completionForm.executorName = userStore.user?.displayName || ''
  completionForm.note = ''
  completionOpen.value = true
}
function openCorrection() {
  if (!detail.value?.completion) return
  Object.assign(correctionForm, {
    result: detail.value.completion.result,
    executedAt: detail.value.completion.executedAt?.slice(0, 16) || asInputDateTime(),
    executorName: detail.value.completion.executorName,
    note: detail.value.completion.note || '',
    reason: '',
  })
  correctionOpen.value = true
}
function openAdHoc() {
  adHocForm.plotId = filters.plotId || plotOptions.value[0]?.plotId || ''
  adHocForm.taskType = '巡园'
  adHocForm.title = ''
  adHocForm.executedAt = asInputDateTime()
  adHocForm.executorName = userStore.user?.displayName || ''
  adHocForm.note = ''
  adHocOpen.value = true
}
async function submitCompletion() {
  if (!detail.value) return
  submitting.value = true
  try {
    await completeTask(detail.value.id, { ...completionForm, executedAt: asUtc(completionForm.executedAt), note: completionForm.note || null })
    completionOpen.value = false
    ElMessage.success('已登记完成记录')
    await openTask(detail.value)
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message || '完成记录提交失败')
  } finally {
    submitting.value = false
  }
}
async function submitCorrection() {
  if (!detail.value || !correctionForm.reason.trim()) return ElMessage.warning('请填写更正原因')
  submitting.value = true
  try {
    await correctTaskCompletion(detail.value.id, { ...correctionForm, executedAt: asUtc(correctionForm.executedAt), note: correctionForm.note || null, reason: correctionForm.reason.trim() })
    correctionOpen.value = false
    ElMessage.success('已追加完成记录更正')
    await openTask(detail.value)
  } catch (error) {
    ElMessage.error(error.message || '完成记录更正失败')
  } finally { submitting.value = false }
}
async function submitAdHoc() {
  if (!adHocForm.plotId) return ElMessage.warning('请选择地块')
  submitting.value = true
  try {
    await createAdHocTask(adHocForm.plotId, { taskType: adHocForm.taskType, title: adHocForm.title, executedAt: asUtc(adHocForm.executedAt), executorName: adHocForm.executorName, note: adHocForm.note || null })
    adHocOpen.value = false
    ElMessage.success('计划外农事已登记')
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message || '计划外农事登记失败')
  } finally {
    submitting.value = false
  }
}

watch(headerPlotId, loadHeaderProductionContext, { immediate: true })
watch(() => farmerStore.selectedFarmId, async () => {
  filters.plotId = farmerStore.selectedPlotId || farmerStore.farmPlots[0]?.plotId || ''
  await loadTasks()
})
watch(calendarDate, async (date) => {
  const month = dateKey(date).slice(0, 7)
  if (month === filters.month) return
  filters.month = month
  if (activeScope.value === 'month') await loadTasks()
})
onMounted(loadTasks)
</script>

<template>
  <div class="farmer-page tasks-page">
    <div class="page-head tasks-head">
      <div>
        <h1 class="page-title">我的农事</h1>
        <p class="page-subtitle task-page-subtitle">按计划执行农事，记录每一次现场管理</p>
      </div>
      <div class="page-actions">
        <el-button type="success" size="large" @click="openAdHoc"><el-icon><Plus /></el-icon>登记计划外农事</el-button>
      </div>
    </div>

    <div class="management-stage-note">
      <span class="stage-note-icon"><PlotOverviewIcon type="management" /></span>
      <span>当前管理阶段：</span>
      <strong>{{ managementStageName }}</strong>
      <template v-if="managementStagePeriod"><i></i><span>{{ managementStagePeriod }}</span></template>
    </div>

    <div class="task-summary">
      <span><span class="summary-icon"><TaskSummaryIcon type="completed" /></span><small>已完成任务</small><b>{{ taskCounts.completed }} <em>项</em></b></span>
      <span class="summary-pending"><span class="summary-icon"><TaskSummaryIcon type="pending" /></span><small>待完成任务</small><b>{{ taskCounts.pending }} <em>项</em></b></span>
      <span class="summary-danger"><span class="summary-icon"><TaskSummaryIcon type="overdue" /></span><small>逾期任务</small><b>{{ taskCounts.overdue }} <em>项</em></b></span>
    </div>

    <section class="content-panel task-workspace">
      <div class="task-toolbar">
        <div class="scope-tabs" role="tablist" aria-label="任务时间范围">
          <button v-for="scope in scopes" :key="scope.key" :class="{ active: activeScope === scope.key }" @click="changeScope(scope.key)">{{ scope.label }}</button>
        </div>
        <div class="task-filters">
          <el-select v-model="filters.plotId" clearable placeholder="全部地块" @change="loadTasks">
            <el-option v-for="plot in plotOptions" :key="plot.plotId" :label="plot.plotName" :value="plot.plotId" />
          </el-select>
          <el-select v-model="filters.status" clearable placeholder="全部状态" @change="loadTasks">
            <el-option label="待处理" value="pending" /><el-option label="进行中" value="in_progress" />
            <el-option label="已逾期" value="overdue" /><el-option label="已完成" value="completed" /><el-option label="已取消" value="cancelled" />
          </el-select>
          <el-date-picker v-if="activeScope === 'month'" v-model="filters.month" type="month" value-format="YYYY-MM" placeholder="选择月份" @change="changeCalendarFilter" />
        </div>
      </div>

      <el-skeleton v-if="loading" :rows="7" animated />
      <template v-else>
        <section v-if="activeScope === 'month'" class="month-calendar">
          <el-calendar v-model="calendarDate">
            <template #header>
              <div class="calendar-head"><div><span>橙园农事月历</span><strong>{{ calendarTitle }}</strong></div><div class="calendar-actions"><el-button text @click="changeCalendarMonth(-1)">上个月</el-button><el-button text @click="goCalendarToday">回到今天</el-button><el-button text @click="changeCalendarMonth(1)">下个月</el-button></div></div>
            </template>
            <template #date-cell="{ data }">
              <div :class="['calendar-cell', { today: isToday(data.day), actionable: dayTasks(data.day).length }]">
                <span class="day-number">{{ Number(data.day.slice(-2)) }}</span>
                <div class="day-tasks">
                  <button v-for="task in dayTasks(data.day).slice(0, 2)" :key="task.id" type="button" :class="['calendar-task', calendarTaskTone(task)]" :title="calendarTaskTitle(task)" @click.stop="openTask(task)">{{ calendarTaskTitle(task) }}</button>
                  <small v-if="dayTasks(data.day).length > 2">另有 {{ dayTasks(data.day).length - 2 }} 项</small>
                </div>
              </div>
            </template>
          </el-calendar>
        </section>
        <div v-else-if="visibleTasks.length" class="task-list">
          <article v-for="task in visibleTasks" :key="task.id" :class="['task-list-item', { completed: task.status === 'completed' }]">
            <span class="task-check" aria-hidden="true"><el-icon v-if="task.status === 'completed'"><Check /></el-icon></span>
            <div class="task-list-main">
              <div class="task-list-title"><strong>{{ task.title }}</strong><span>{{ sourceLabel(task.source) }}</span></div>
              <div class="task-list-meta">
                <span>地块：{{ task.plotName }}</span><i></i>
                <span>农场：{{ taskFarmName(task) }}</span><i></i>
                <span>建议日期：{{ formatDate(task.scheduledDate) }}</span>
              </div>
            </div>
            <span class="task-stage">{{ taskStageLabel(task) }}</span>
            <button v-if="isActionable(task)" class="go-complete" @click="openTask(task)">去完成 <el-icon><ArrowRight /></el-icon></button>
            <span v-else :class="['task-finished-state', statusTone(task.status)]">{{ statusLabel(task.status) }}</span>
          </article>
        </div>
        <el-empty v-else :image-size="82" description="当前没有农事任务" />
      </template>
    </section>

    <el-drawer v-model="drawerOpen" size="min(500px, 94vw)" direction="rtl" :with-header="false" @closed="closeDrawer">
      <el-skeleton v-if="detailLoading" :rows="12" animated />
      <template v-else-if="detail">
        <div class="drawer-head"><div><span class="drawer-eyebrow">{{ detail.plotName }}</span><h2>{{ detail.title }}</h2><p>{{ detail.stageCode || '现场农事' }} · {{ sourceLabel(detail.source) }}</p></div><button class="drawer-close" @click="closeDrawer"><el-icon><Close /></el-icon></button></div>
        <div class="drawer-status"><span :class="['task-status', statusTone(detail.status)]">{{ statusLabel(detail.status) }}</span><span>建议日期 {{ formatDate(detail.scheduledDate) }}</span></div>
        <dl class="task-facts"><div><dt>任务类型</dt><dd>{{ detail.taskType }}</dd></div><div><dt>计划来源</dt><dd>{{ sourceLabel(detail.source) }}</dd></div><div class="fact-wide"><dt>任务备注</dt><dd>{{ detail.note || '无' }}</dd></div></dl>
        <section class="record-section plan-context"><div class="record-title"><el-icon><Clock /></el-icon><strong>计划依据</strong></div><template v-if="detail.source === 'ad_hoc'"><p class="context-empty">这是农户对已完成计划外农事的现场补录，不对应模板任务。</p></template><template v-else-if="detail.source === 'temporary'"><p class="context-empty">这是农场管理员针对当前阶段新增的临时任务，不改变年度管理计划基线。</p></template><template v-else-if="detail.source === 'planting'"><p class="context-summary">这是全园定植任务。完成后会计入果园定植进度；全部有效地块完成后，系统自动写入果园实际定植日期并启用后续年度建议。</p></template><template v-else-if="productionContext"><p class="context-summary">依据 {{ productionContext.templateName }}（{{ productionContext.crop }}，V{{ productionContext.versionNo }}）的 {{ productionContext.productionYear }} 生产年度和全园{{ productionContext.track === 'young' ? '幼树' : '结果树' }}轨道生成，由农场管理员统一下发。</p><dl v-if="productionContext.stage"><div><dt>当前阶段</dt><dd>{{ productionContext.stage.name }}</dd></div><div><dt>阶段周期</dt><dd>{{ productionContext.stage.startsOn }} 至 {{ productionContext.stage.endsOn }}</dd></div><div class="context-wide"><dt>管理重点</dt><dd>{{ productionContext.stage.managementFocus || '暂无' }}</dd></div><div v-if="productionContext.stage.moistureMin !== null || productionContext.stage.moistureMax !== null" class="context-wide"><dt>土壤湿度建议</dt><dd>{{ productionContext.stage.moistureMin ?? '-' }}% 至 {{ productionContext.stage.moistureMax ?? '-' }}%</dd></div></dl><p v-else class="context-empty">当前日期不在模板定义的物候阶段内。</p></template><p v-else class="context-empty">{{ productionContextError || '正在读取年度生产资料' }}</p></section>
        <div v-if="canExecute" class="drawer-commands"><el-button type="success" @click="openCompletion"><el-icon><CircleCheck /></el-icon>完成农事</el-button></div>
        <section v-if="detail.completion" class="record-section completion-record"><div class="record-title"><el-icon><CircleCheckFilled /></el-icon><strong>完成记录</strong><el-button link type="primary" @click="openCorrection">追加更正</el-button></div><dl><div><dt>执行时间</dt><dd>{{ formatDateTime(detail.completion.executedAt) }}</dd></div><div><dt>执行人</dt><dd>{{ detail.completion.executorName }}</dd></div><div><dt>执行结果</dt><dd>{{ detail.completion.result }}</dd></div><div class="record-wide"><dt>现场备注</dt><dd>{{ detail.completion.note || '无' }}</dd></div></dl><div v-if="detail.completionHistory?.length > 1" class="completion-history"><small>原始记录及后续更正</small><div v-for="item in detail.completionHistory" :key="item.id"><strong>{{ item.recordType === 'correction' ? '更正记录' : '原始记录' }}</strong><span>{{ formatDateTime(item.createdAt) }}</span></div></div></section>
        <section class="record-section"><div class="record-title"><el-icon><Clock /></el-icon><strong>任务记录</strong></div><div v-if="detail.adjustments?.length" class="history-list"><div v-for="item in detail.adjustments" :key="item.id" class="history-item"><span class="history-dot"></span><div><strong>{{ item.type === 'completion' ? '登记完成' : '历史调整' }}</strong><p>{{ formatDateTime(item.createdAt) }}</p></div></div></div><el-empty v-else :image-size="46" description="暂无任务记录" /></section>
      </template>
    </el-drawer>

    <el-dialog v-model="completionOpen" title="完成农事" width="min(520px, 92vw)" destroy-on-close>
      <el-form label-position="top"><el-form-item label="执行结果"><el-input v-model="completionForm.result" maxlength="255" /></el-form-item><el-form-item label="执行时间"><el-date-picker v-model="completionForm.executedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm" /></el-form-item><el-form-item label="执行人"><el-input v-model="completionForm.executorName" maxlength="50" /></el-form-item><el-form-item label="现场备注"><el-input v-model="completionForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit /></el-form-item></el-form>
      <template #footer><el-button @click="completionOpen = false">取消</el-button><el-button type="success" :loading="submitting" @click="submitCompletion">确认完成</el-button></template>
    </el-dialog>
    <el-dialog v-model="correctionOpen" title="追加完成记录更正" width="min(520px, 92vw)" destroy-on-close>
      <el-form label-position="top"><el-form-item label="更正后执行结果"><el-input v-model="correctionForm.result" maxlength="255" /></el-form-item><el-form-item label="更正后执行时间"><el-date-picker v-model="correctionForm.executedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm" /></el-form-item><el-form-item label="执行人"><el-input v-model="correctionForm.executorName" maxlength="50" /></el-form-item><el-form-item label="现场备注"><el-input v-model="correctionForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit /></el-form-item><el-form-item label="更正原因" required><el-input v-model="correctionForm.reason" type="textarea" :rows="2" maxlength="500" show-word-limit /></el-form-item></el-form>
      <template #footer><el-button @click="correctionOpen = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submitCorrection">确认追加</el-button></template>
    </el-dialog>

    <el-dialog v-model="adHocOpen" title="登记计划外农事" width="min(560px, 92vw)" destroy-on-close>
      <el-form label-position="top"><el-form-item label="地块"><el-select v-model="adHocForm.plotId" placeholder="选择地块"><el-option v-for="plot in plotOptions" :key="plot.plotId" :label="plot.plotName" :value="plot.plotId" /></el-select></el-form-item><el-form-item label="农事类型"><el-select v-model="adHocForm.taskType"><el-option v-for="item in ['巡园', '修剪', '施肥', '除草', '病虫害处置', '其他']" :key="item" :label="item" :value="item" /></el-select></el-form-item><el-form-item label="农事名称"><el-input v-model="adHocForm.title" maxlength="150" /></el-form-item><el-form-item label="执行时间"><el-date-picker v-model="adHocForm.executedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm" /></el-form-item><el-form-item label="执行人"><el-input v-model="adHocForm.executorName" maxlength="50" /></el-form-item><el-form-item label="现场备注"><el-input v-model="adHocForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit /></el-form-item></el-form>
      <template #footer><el-button @click="adHocOpen = false">取消</el-button><el-button type="success" :loading="submitting" @click="submitAdHoc">确认登记</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tasks-head{align-items:flex-start;margin-bottom:0}.task-page-subtitle{margin:7px 0 0}.tasks-head .page-actions :deep(.el-button){min-width:196px;height:52px;padding:0 24px;font-size:16px}.management-stage-note{display:flex;align-items:center;gap:5px;margin:22px 0 14px;color:#68766f;font-size:14px}.management-stage-note strong{color:#25362e;font-size:15px}.management-stage-note i{width:1px;height:16px;margin:0 8px;background:#b9c0bc}.stage-note-icon{width:22px;height:22px;display:grid;place-items:center;margin-right:2px;border-radius:5px;color:#287e48;background:#eff6eb}.task-summary{width:100%;min-height:136px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));margin:0 0 18px;padding:20px 0;border:1px solid #e8ece7;border-radius:10px;background:#fff;box-shadow:0 7px 20px rgba(24,65,45,.045)}.task-summary>span{display:grid;grid-template-columns:64px auto;grid-template-rows:auto auto;align-content:center;justify-content:center;column-gap:22px;padding:0 34px;border-right:1px solid #e5eae5}.task-summary>span:last-child{border-right:0}.task-summary .el-icon{grid-row:1/3;display:grid;width:64px;height:64px;place-items:center;border-radius:14px;color:#267b45;background:#edf6ea;font-size:34px}.task-summary small{align-self:end;color:#46524b;font-size:15px;line-height:1.2}.task-summary b{align-self:start;margin-top:8px;color:#18703c;font-size:31px;line-height:1}.task-summary em{font-size:16px;font-style:normal}.task-summary .summary-progress .el-icon{color:#d89105;background:#fff6e5}.task-summary .summary-progress b{color:#d68a00}.task-summary .summary-danger .el-icon{color:#de3d31;background:#fcebea}.task-summary .summary-danger b{color:#dc3a30}.task-workspace{min-height:480px}.task-toolbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px}.scope-tabs{display:flex;gap:4px;padding:4px;border:1px solid #dce9e3;border-radius:10px;background:#f4f8f6}.scope-tabs button{height:34px;padding:0 13px;border:0;border-radius:7px;color:#6c8178;background:transparent;cursor:pointer}.scope-tabs button:hover{color:#257a58}.scope-tabs button.active{color:#fff;background:#277f5c;box-shadow:0 3px 8px rgba(30,107,76,.18)}.task-filters{display:flex;gap:9px}.task-filters .el-select{width:145px}.task-filters :deep(.el-date-editor){width:135px}.task-table{cursor:pointer}.date-label{color:#315447;font-size:13px}.date-help{display:block;margin-top:5px;color:#84938d;font-size:11px}.task-title{display:grid;gap:4px}.task-title strong{color:#274438;font-size:14px}.task-title span{color:#82928c;font-size:11px}.task-actions{display:flex;align-items:center;gap:4px}.task-actions :deep(.el-button){margin:0}.task-status{display:inline-flex;align-items:center;justify-content:center;min-width:66px;padding:5px 8px;border-radius:7px;color:#5e746a;background:#f0f4f2;font-size:11px}.task-status.success{color:#287d5a;background:#e8f6ee}.task-status.warning{color:#a96c25;background:#fff3df}.task-status.danger{color:#b84f4f;background:#fbeaea}.task-status.info{color:#69807b;background:#edf1f1}.drawer-head{display:flex;justify-content:space-between;gap:16px;padding:6px 2px 18px;border-bottom:1px solid #e5eee9}.drawer-eyebrow{color:#25815d;font-size:12px;font-weight:700}.drawer-head h2{margin:8px 0 5px;color:#254337;font-size:23px}.drawer-head p{margin:0;color:#7d8d87;font-size:12px}.drawer-close{width:34px;height:34px;display:grid;place-items:center;border:1px solid #dce8e2;border-radius:9px;color:#60766d;background:#fafcfb;cursor:pointer}.drawer-status{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:16px 0;color:#70827b;font-size:12px}.task-facts{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0}.task-facts>div{padding:12px;border:1px solid #e3ece7;border-radius:9px;background:#f8fbf9}.task-facts .fact-wide{grid-column:1/-1}.task-facts dt,.record-section dt{margin-bottom:5px;color:#8a9993;font-size:11px}.task-facts dd,.record-section dd{margin:0;color:#345247;font-size:13px;line-height:1.55}.drawer-commands{display:flex;gap:10px;margin:18px 0}.drawer-commands .el-button{flex:1}.record-section{margin-top:22px;padding-top:18px;border-top:1px solid #e6eee9}.record-title{display:flex;align-items:center;gap:7px;margin-bottom:12px;color:#355447}.record-title .el-icon{color:#2d9368}.completion-record dl{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:0}.completion-record dl>div{padding:10px 0;border-bottom:1px solid #eff4f1}.completion-record .record-wide{grid-column:1/-1}.history-list{display:grid;gap:12px}.history-item{position:relative;display:flex;gap:10px;padding-left:3px}.history-item:not(:last-child)::before{position:absolute;top:20px;bottom:-13px;left:7px;width:1px;content:'';background:#dce9e3}.history-dot{width:9px;height:9px;flex:0 0 9px;margin-top:4px;border-radius:50%;background:#48a97b;box-shadow:0 0 0 4px #e6f5ed}.history-item strong{color:#3c5b50;font-size:12px}.history-item p{margin:3px 0 0;color:#9aa7a1;font-size:11px}.plan-context{margin-top:18px}.context-summary,.context-empty{margin:0;color:#60776d;font-size:12px;line-height:1.75}.plan-context dl{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0 0}.plan-context dl>div{padding:10px;border:1px solid #e3ece7;border-radius:8px;background:#f8fbf9}.plan-context .context-wide{grid-column:1/-1}.plan-context dt{margin-bottom:4px;color:#8a9993;font-size:11px}.plan-context dd{margin:0;color:#345247;font-size:13px;line-height:1.55}@media(max-width:820px){.task-summary>span{grid-template-columns:48px auto;column-gap:12px;padding:0 14px}.task-summary .el-icon{width:48px;height:48px;font-size:27px}.task-toolbar{align-items:stretch;flex-direction:column}.task-filters{flex-wrap:wrap}.task-filters .el-select{flex:1;min-width:130px}.task-table :deep(.el-table__cell:nth-child(2)),.task-table :deep(.el-table__cell:nth-child(4)){display:none}}@media(max-width:520px){.task-summary{grid-template-columns:1fr;min-height:0;padding:5px 18px}.task-summary>span,.task-summary>span:first-child,.task-summary>span:last-child{justify-content:start;padding:14px 0;border-right:0;border-bottom:1px solid #e5eae5}.task-summary>span:last-child{border-bottom:0}.management-stage-note{align-items:flex-start;flex-wrap:wrap;margin-top:16px}.tasks-head .page-actions :deep(.el-button){width:100%}.scope-tabs{width:100%;justify-content:space-between}.scope-tabs button{padding:0 8px;font-size:11px}.task-filters{display:grid;grid-template-columns:1fr 1fr}.task-filters .el-select,.task-filters :deep(.el-date-editor){width:100%}.completion-record dl,.task-facts,.plan-context dl{grid-template-columns:1fr}.completion-record .record-wide,.task-facts .fact-wide,.plan-context .context-wide{grid-column:auto}.drawer-commands{flex-direction:column}}
.tasks-page{margin-top:-10px}.management-stage-note{gap:7px;color:#66726c;font-size:15px;line-height:1.4}.management-stage-note strong{color:#202e27;font-size:16px;font-weight:700}.management-stage-note i{height:17px;background:#aeb7b2}.stage-note-icon{width:26px;height:26px;margin-right:1px;border-radius:6px}.stage-note-icon :deep(svg){width:18px;height:18px;stroke-width:2.2}.task-summary .summary-icon{grid-row:1/3;width:64px;height:64px;display:grid;place-items:center;border-radius:14px;color:#267b45;background:#edf6ea}.task-summary .summary-icon :deep(svg){width:34px;height:34px}.task-summary .summary-pending .summary-icon{color:#d89105;background:#fff6e5}.task-summary .summary-pending b{color:#d68a00}.task-summary .summary-danger .summary-icon{color:#d9362c;background:#fcebea}.task-toolbar{min-height:64px;margin:-20px -20px 20px;padding:0 20px;border-bottom:1px solid #e5e9e6}.scope-tabs{align-self:stretch;gap:36px;padding:0;border:0;border-radius:0;background:transparent}.scope-tabs button{position:relative;height:64px;padding:0 4px;border:0;border-radius:0;color:#4f5d56;background:transparent;font-size:15px;font-weight:500}.scope-tabs button:hover{color:#217a43;background:transparent}.scope-tabs button.active{color:#16733a;background:transparent;box-shadow:none;font-weight:700}.scope-tabs button.active::after{position:absolute;right:0;bottom:0;left:0;height:3px;border-radius:3px 3px 0 0;content:'';background:#16733a}.task-list{display:grid;gap:10px}.task-list-item{min-height:92px;display:grid;grid-template-columns:28px minmax(0,1fr) minmax(130px,220px) 126px;align-items:center;gap:18px;padding:16px 20px;border:1px solid #e5e9e6;border-radius:8px;background:#fff}.task-list-item:hover{border-color:#cddbd1;box-shadow:0 3px 10px rgba(28,69,48,.04)}.task-check{width:24px;height:24px;display:grid;place-items:center;border:2px solid #bdc5c0;border-radius:4px;color:#fff;background:#fff}.task-check .el-icon{font-size:17px;font-weight:700}.task-list-item.completed .task-check{border-color:#43852d;background:#43852d}.task-list-main{min-width:0;display:grid;gap:9px}.task-list-title{display:flex;align-items:center;gap:12px;min-width:0}.task-list-title strong{overflow:hidden;color:#17241e;font-size:16px;text-overflow:ellipsis;white-space:nowrap}.task-list-title>span{flex:0 0 auto;padding:4px 9px;border-radius:6px;color:#2e7b3c;background:#eff7e6;font-size:12px}.task-list-meta{display:flex;align-items:center;gap:12px;min-width:0;color:#68746e;font-size:13px;white-space:nowrap}.task-list-meta i{width:1px;height:15px;flex:0 0 1px;background:#d9dfdb}.task-stage{justify-self:end;color:#65716b;font-size:13px;text-align:right}.go-complete{width:126px;height:44px;display:flex;align-items:center;justify-content:center;gap:12px;border:1px solid #2b7d45;border-radius:7px;color:#21763d;background:transparent;font-size:14px;font-weight:700;cursor:pointer}.go-complete:hover{color:#155f31;background:#f7fbf7;border-color:#155f31}.go-complete .el-icon{font-size:18px}.task-finished-state{width:126px;justify-self:end;color:#2b7d45;font-size:14px;font-weight:700;text-align:center}.task-finished-state.info{color:#75817b}@media(max-width:1050px){.task-list-item{grid-template-columns:28px minmax(0,1fr) 116px}.task-stage{display:none}.task-list-meta{flex-wrap:wrap;white-space:normal}.task-list-meta i{display:none}}@media(max-width:820px){.task-summary .summary-icon{width:48px;height:48px}.task-summary .summary-icon :deep(svg){width:27px;height:27px}.scope-tabs{gap:18px}.task-list-item{gap:12px;padding:14px}.go-complete,.task-finished-state{width:110px}}@media(max-width:620px){.task-list-item{grid-template-columns:24px minmax(0,1fr);align-items:start}.go-complete,.task-finished-state{grid-column:2;width:100%;height:40px}.task-list-meta{display:grid;gap:5px}.task-check{width:22px;height:22px;margin-top:2px}}@media(max-width:520px){.task-toolbar{margin:-16px -16px 16px;padding:0 16px}.scope-tabs{gap:0}.scope-tabs button{height:52px}}
.month-calendar{overflow:hidden;margin:-1px;border:1px solid #dfe7dc;border-radius:8px;background:rgba(255,255,255,.72)}.month-calendar :deep(.el-calendar){background:transparent}.month-calendar :deep(.el-calendar__header){padding:17px 20px 13px;border-bottom:1px solid #e2e9df}.month-calendar :deep(.el-calendar__body){padding:9px 12px 16px}.month-calendar :deep(.el-calendar-table th){padding:9px;color:#647b6c;font-size:0!important;font-weight:700}.month-calendar :deep(.el-calendar-table th::after){font-size:12px!important}.month-calendar :deep(.el-calendar-table th:nth-child(1)::after){content:'周日'}.month-calendar :deep(.el-calendar-table th:nth-child(2)::after){content:'周一'}.month-calendar :deep(.el-calendar-table th:nth-child(3)::after){content:'周二'}.month-calendar :deep(.el-calendar-table th:nth-child(4)::after){content:'周三'}.month-calendar :deep(.el-calendar-table th:nth-child(5)::after){content:'周四'}.month-calendar :deep(.el-calendar-table th:nth-child(6)::after){content:'周五'}.month-calendar :deep(.el-calendar-table th:nth-child(7)::after){content:'周六'}.month-calendar :deep(.el-calendar-table td){border-color:#e4e9e2}.month-calendar :deep(.el-calendar-day){height:104px;padding:5px}.month-calendar :deep(.el-calendar-table td.is-selected){background:#f0f6ec}.calendar-head{width:100%;display:flex;align-items:center;justify-content:space-between;gap:16px}.calendar-head>div:first-child{display:flex;flex-direction:column;gap:3px}.calendar-head span{color:#4a8c5e;font-size:11px;letter-spacing:.08em}.calendar-head strong{color:#25382f;font-size:19px}.calendar-actions{display:flex;align-items:center}.calendar-cell{height:100%;position:relative}.day-number{width:25px;height:25px;display:grid;place-items:center;border-radius:50%;color:#5f7166;font-size:12px}.calendar-cell.today .day-number{color:#fff;background:#237a43}.day-tasks{display:grid;gap:3px;margin-top:4px}.calendar-task{max-width:100%;overflow:hidden;padding:3px 5px;border:0;border-left:2px solid #d58a45;border-radius:3px;color:#66523f;background:#fff1dd;font-size:9px;text-align:left;text-overflow:ellipsis;white-space:nowrap;cursor:pointer}.calendar-task:hover{filter:brightness(.97)}.calendar-task.blue{border-color:#6499c8;background:#e9f3fb;color:#3f627d}.calendar-task.green{border-color:#58a16f;background:#e9f5e8;color:#416c4b}.calendar-task.rose{border-color:#c76e6e;background:#faeaea;color:#835050}.calendar-task.purple{border-color:#8f7bb2;background:#f0ebf7;color:#605477}.calendar-task.muted{border-color:#9aa59e;background:#eff2ef;color:#7c8780;text-decoration:line-through}.day-tasks small{color:#839087;font-size:8px}@media(max-width:760px){.calendar-head{align-items:flex-start;flex-direction:column}.calendar-actions{width:100%;justify-content:space-between}.calendar-actions .el-button{margin:0}.month-calendar :deep(.el-calendar-day){height:82px}.calendar-task{max-width:72px}}
</style>
