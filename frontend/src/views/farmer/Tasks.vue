<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createAdHocTask, completeTask, getTask, listTasks, updateTask } from '@/api/task'
import { getPlotProductionContext } from '@/api/production'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'
import { formatDateTime as formatLocalDateTime } from '@/utils/dataAdapters'

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
const drawerOpen = ref(false)
const adjustOpen = ref(false)
const completionOpen = ref(false)
const adHocOpen = ref(false)
const submitting = ref(false)
const filters = reactive({ plotId: '', status: '', month: new Date().toISOString().slice(0, 7) })
const editForm = reactive({ scheduledDate: '', note: '', status: 'pending' })
const completionForm = reactive({ result: '已完成', executedAt: '', executorName: '', note: '' })
const adHocForm = reactive({ plotId: '', taskType: '巡园', title: '', executedAt: '', executorName: '', note: '' })

const visibleTasks = computed(() => tasks.value)
const taskCounts = computed(() => ({
  pending: tasks.value.filter((item) => item.status === 'pending').length,
  inProgress: tasks.value.filter((item) => item.status === 'in_progress').length,
  overdue: tasks.value.filter((item) => item.status === 'overdue').length,
  completed: tasks.value.filter((item) => item.status === 'completed').length,
}))
const plotOptions = computed(() => farmerStore.accessiblePlots || [])
const canExecute = computed(() => detail.value && !['completed', 'cancelled'].includes(detail.value.status))

function statusLabel(status) {
  return ({ pending: '待处理', in_progress: '进行中', completed: '已完成', overdue: '已逾期', cancelled: '已取消' })[status] || status
}
function statusTone(status) {
  return ({ overdue: 'danger', cancelled: 'info', in_progress: 'warning', completed: 'success', pending: 'neutral' })[status] || 'neutral'
}
function sourceLabel(source) { return source === 'ad_hoc' ? '计划外' : source === 'planting' ? '定植任务' : '计划任务' }
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

async function loadTasks() {
  loading.value = true
  try {
    const params = { scope: activeScope.value }
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
function openAdjust() {
  editForm.scheduledDate = detail.value.scheduledDate
  editForm.note = detail.value.note || ''
  editForm.status = detail.value.status === 'overdue' ? 'pending' : detail.value.status
  adjustOpen.value = true
}
function openCompletion() {
  completionForm.result = '已完成'
  completionForm.executedAt = asInputDateTime()
  completionForm.executorName = userStore.user?.displayName || ''
  completionForm.note = ''
  completionOpen.value = true
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
async function submitAdjust() {
  if (!detail.value) return
  submitting.value = true
  try {
    await updateTask(detail.value.id, { scheduledDate: editForm.scheduledDate, note: editForm.note || null, status: editForm.status })
    adjustOpen.value = false
    ElMessage.success('任务已调整')
    await openTask(detail.value)
    await loadTasks()
  } catch (error) {
    ElMessage.error(error.message || '任务调整失败')
  } finally {
    submitting.value = false
  }
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

onMounted(loadTasks)
</script>

<template>
  <div class="farmer-page tasks-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">我的农事</h1>
        <div class="task-summary">
          <span>待处理 <b>{{ taskCounts.pending }}</b></span>
          <span>进行中 <b>{{ taskCounts.inProgress }}</b></span>
          <span class="summary-danger">逾期 <b>{{ taskCounts.overdue }}</b></span>
        </div>
      </div>
      <div class="page-actions">
        <el-button type="success" size="large" @click="openAdHoc"><el-icon><Plus /></el-icon>登记农事</el-button>
      </div>
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
          <el-date-picker v-if="activeScope === 'month'" v-model="filters.month" type="month" value-format="YYYY-MM" placeholder="选择月份" @change="loadTasks" />
        </div>
      </div>

      <el-skeleton v-if="loading" :rows="7" animated />
      <template v-else>
        <el-table v-if="visibleTasks.length" :data="visibleTasks" class="compact-table task-table" @row-click="openTask">
          <el-table-column label="建议日期" width="118"><template #default="scope"><strong class="date-label">{{ formatDate(scope.row.scheduledDate) }}</strong></template></el-table-column>
          <el-table-column prop="plotName" label="地块" min-width="120" />
          <el-table-column label="农事任务" min-width="240"><template #default="scope"><div class="task-title"><strong>{{ scope.row.title }}</strong><span>{{ scope.row.stageCode || '现场农事' }} · {{ sourceLabel(scope.row.source) }}</span></div></template></el-table-column>
          <el-table-column label="状态" width="112"><template #default="scope"><span :class="['task-status', statusTone(scope.row.status)]">{{ statusLabel(scope.row.status) }}</span></template></el-table-column>
          <el-table-column label="操作" width="192" fixed="right"><template #default="scope"><div class="task-actions" @click.stop><el-button size="small" text type="primary" @click="openTask(scope.row)">详情</el-button><el-button v-if="isActionable(scope.row)" size="small" type="success" plain @click="openTask(scope.row)">处理</el-button></div></template></el-table-column>
        </el-table>
        <el-empty v-else :image-size="82" description="当前没有农事任务" />
      </template>
    </section>

    <el-drawer v-model="drawerOpen" size="min(500px, 94vw)" direction="rtl" :with-header="false" @closed="closeDrawer">
      <el-skeleton v-if="detailLoading" :rows="12" animated />
      <template v-else-if="detail">
        <div class="drawer-head"><div><span class="drawer-eyebrow">{{ detail.plotName }}</span><h2>{{ detail.title }}</h2><p>{{ detail.stageCode || '现场农事' }} · {{ sourceLabel(detail.source) }}</p></div><button class="drawer-close" @click="closeDrawer"><el-icon><Close /></el-icon></button></div>
        <div class="drawer-status"><span :class="['task-status', statusTone(detail.status)]">{{ statusLabel(detail.status) }}</span><span>建议日期 {{ formatDate(detail.scheduledDate) }}</span></div>
        <dl class="task-facts"><div><dt>任务类型</dt><dd>{{ detail.taskType }}</dd></div><div><dt>计划来源</dt><dd>{{ sourceLabel(detail.source) }}</dd></div><div class="fact-wide"><dt>任务备注</dt><dd>{{ detail.note || '无' }}</dd></div></dl>
        <section class="record-section plan-context"><div class="record-title"><el-icon><Clock /></el-icon><strong>计划依据</strong></div><template v-if="detail.source === 'ad_hoc'"><p class="context-empty">这是计划外农事，由现场实际工作补充登记，不对应模板任务。</p></template><template v-else-if="detail.source === 'planting'"><p class="context-summary">这是全园定植任务。完成后会计入果园定植进度；全部有效地块完成后，系统自动写入果园实际定植日期并启用后续年度建议。</p></template><template v-else-if="productionContext"><p class="context-summary">依据 {{ productionContext.templateName }}（{{ productionContext.crop }}，V{{ productionContext.versionNo }}）的 {{ productionContext.productionYear }} 生产年度和全园{{ productionContext.track === 'young' ? '幼树' : '结果树' }}轨道生成；建议日期可按现场情况调整。</p><dl v-if="productionContext.stage"><div><dt>当前阶段</dt><dd>{{ productionContext.stage.name }}</dd></div><div><dt>阶段周期</dt><dd>{{ productionContext.stage.startsOn }} 至 {{ productionContext.stage.endsOn }}</dd></div><div class="context-wide"><dt>管理重点</dt><dd>{{ productionContext.stage.managementFocus || '暂无' }}</dd></div><div v-if="productionContext.stage.moistureMin !== null || productionContext.stage.moistureMax !== null" class="context-wide"><dt>土壤湿度建议</dt><dd>{{ productionContext.stage.moistureMin ?? '-' }}% 至 {{ productionContext.stage.moistureMax ?? '-' }}%</dd></div></dl><p v-else class="context-empty">当前日期不在模板定义的物候阶段内。</p></template><p v-else class="context-empty">{{ productionContextError || '正在读取年度生产资料' }}</p></section>
        <div v-if="canExecute" class="drawer-commands"><el-button plain @click="openAdjust"><el-icon><EditPen /></el-icon>调整任务</el-button><el-button type="success" @click="openCompletion"><el-icon><CircleCheck /></el-icon>完成农事</el-button></div>
        <section v-if="detail.completion" class="record-section completion-record"><div class="record-title"><el-icon><CircleCheckFilled /></el-icon><strong>完成记录</strong></div><dl><div><dt>执行时间</dt><dd>{{ formatDateTime(detail.completion.executedAt) }}</dd></div><div><dt>执行人</dt><dd>{{ detail.completion.executorName }}</dd></div><div><dt>执行结果</dt><dd>{{ detail.completion.result }}</dd></div><div class="record-wide"><dt>现场备注</dt><dd>{{ detail.completion.note || '无' }}</dd></div></dl></section>
        <section class="record-section"><div class="record-title"><el-icon><Clock /></el-icon><strong>调整记录</strong></div><div v-if="detail.adjustments?.length" class="history-list"><div v-for="item in detail.adjustments" :key="item.id" class="history-item"><span class="history-dot"></span><div><strong>{{ item.type === 'completion' ? '登记完成' : '调整任务' }}</strong><p>{{ formatDateTime(item.createdAt) }}</p></div></div></div><el-empty v-else :image-size="46" description="暂无调整记录" /></section>
      </template>
    </el-drawer>

    <el-dialog v-model="adjustOpen" title="调整任务" width="min(520px, 92vw)" destroy-on-close>
      <el-form label-position="top"><el-form-item label="建议日期"><el-date-picker v-model="editForm.scheduledDate" type="date" value-format="YYYY-MM-DD" /><small class="date-help">可根据物候、天气和现场情况调整。</small></el-form-item><el-form-item label="任务状态"><el-radio-group v-model="editForm.status"><el-radio-button label="pending">待处理</el-radio-button><el-radio-button label="in_progress">进行中</el-radio-button><el-radio-button label="cancelled">取消</el-radio-button></el-radio-group></el-form-item><el-form-item label="现场备注"><el-input v-model="editForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit /></el-form-item></el-form>
      <template #footer><el-button @click="adjustOpen = false">取消</el-button><el-button type="success" :loading="submitting" @click="submitAdjust">保存调整</el-button></template>
    </el-dialog>

    <el-dialog v-model="completionOpen" title="完成农事" width="min(520px, 92vw)" destroy-on-close>
      <el-form label-position="top"><el-form-item label="执行结果"><el-input v-model="completionForm.result" maxlength="255" /></el-form-item><el-form-item label="执行时间"><el-date-picker v-model="completionForm.executedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm" /></el-form-item><el-form-item label="执行人"><el-input v-model="completionForm.executorName" maxlength="50" /></el-form-item><el-form-item label="现场备注"><el-input v-model="completionForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit /></el-form-item></el-form>
      <template #footer><el-button @click="completionOpen = false">取消</el-button><el-button type="success" :loading="submitting" @click="submitCompletion">确认完成</el-button></template>
    </el-dialog>

    <el-dialog v-model="adHocOpen" title="登记农事" width="min(560px, 92vw)" destroy-on-close>
      <el-form label-position="top"><el-form-item label="地块"><el-select v-model="adHocForm.plotId" placeholder="选择地块"><el-option v-for="plot in plotOptions" :key="plot.plotId" :label="plot.plotName" :value="plot.plotId" /></el-select></el-form-item><el-form-item label="农事类型"><el-select v-model="adHocForm.taskType"><el-option v-for="item in ['巡园', '修剪', '施肥', '除草', '病虫害处置', '其他']" :key="item" :label="item" :value="item" /></el-select></el-form-item><el-form-item label="农事名称"><el-input v-model="adHocForm.title" maxlength="150" /></el-form-item><el-form-item label="执行时间"><el-date-picker v-model="adHocForm.executedAt" type="datetime" value-format="YYYY-MM-DDTHH:mm" /></el-form-item><el-form-item label="执行人"><el-input v-model="adHocForm.executorName" maxlength="50" /></el-form-item><el-form-item label="现场备注"><el-input v-model="adHocForm.note" type="textarea" :rows="3" maxlength="1000" show-word-limit /></el-form-item></el-form>
      <template #footer><el-button @click="adHocOpen = false">取消</el-button><el-button type="success" :loading="submitting" @click="submitAdHoc">确认登记</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.task-summary{display:flex;gap:14px;margin-top:10px;color:#74857e;font-size:12px}.task-summary b{margin-left:3px;color:#27483c;font-size:15px}.summary-danger b{color:#bd5656}.task-workspace{min-height:480px}.task-toolbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px}.scope-tabs{display:flex;gap:4px;padding:4px;border:1px solid #dce9e3;border-radius:10px;background:#f4f8f6}.scope-tabs button{height:34px;padding:0 13px;border:0;border-radius:7px;color:#6c8178;background:transparent;cursor:pointer}.scope-tabs button:hover{color:#257a58}.scope-tabs button.active{color:#fff;background:#277f5c;box-shadow:0 3px 8px rgba(30,107,76,.18)}.task-filters{display:flex;gap:9px}.task-filters .el-select{width:145px}.task-filters :deep(.el-date-editor){width:135px}.task-table{cursor:pointer}.date-label{color:#315447;font-size:13px}.date-help{display:block;margin-top:5px;color:#84938d;font-size:11px}.task-title{display:grid;gap:4px}.task-title strong{color:#274438;font-size:14px}.task-title span{color:#82928c;font-size:11px}.task-actions{display:flex;align-items:center;gap:4px}.task-actions :deep(.el-button){margin:0}.task-status{display:inline-flex;align-items:center;justify-content:center;min-width:66px;padding:5px 8px;border-radius:7px;color:#5e746a;background:#f0f4f2;font-size:11px}.task-status.success{color:#287d5a;background:#e8f6ee}.task-status.warning{color:#a96c25;background:#fff3df}.task-status.danger{color:#b84f4f;background:#fbeaea}.task-status.info{color:#69807b;background:#edf1f1}.drawer-head{display:flex;justify-content:space-between;gap:16px;padding:6px 2px 18px;border-bottom:1px solid #e5eee9}.drawer-eyebrow{color:#25815d;font-size:12px;font-weight:700}.drawer-head h2{margin:8px 0 5px;color:#254337;font-size:23px}.drawer-head p{margin:0;color:#7d8d87;font-size:12px}.drawer-close{width:34px;height:34px;display:grid;place-items:center;border:1px solid #dce8e2;border-radius:9px;color:#60766d;background:#fafcfb;cursor:pointer}.drawer-status{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:16px 0;color:#70827b;font-size:12px}.task-facts{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0}.task-facts>div{padding:12px;border:1px solid #e3ece7;border-radius:9px;background:#f8fbf9}.task-facts .fact-wide{grid-column:1/-1}.task-facts dt,.record-section dt{margin-bottom:5px;color:#8a9993;font-size:11px}.task-facts dd,.record-section dd{margin:0;color:#345247;font-size:13px;line-height:1.55}.drawer-commands{display:flex;gap:10px;margin:18px 0}.drawer-commands .el-button{flex:1}.record-section{margin-top:22px;padding-top:18px;border-top:1px solid #e6eee9}.record-title{display:flex;align-items:center;gap:7px;margin-bottom:12px;color:#355447}.record-title .el-icon{color:#2d9368}.completion-record dl{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:0}.completion-record dl>div{padding:10px 0;border-bottom:1px solid #eff4f1}.completion-record .record-wide{grid-column:1/-1}.history-list{display:grid;gap:12px}.history-item{position:relative;display:flex;gap:10px;padding-left:3px}.history-item:not(:last-child)::before{position:absolute;top:20px;bottom:-13px;left:7px;width:1px;content:'';background:#dce9e3}.history-dot{width:9px;height:9px;flex:0 0 9px;margin-top:4px;border-radius:50%;background:#48a97b;box-shadow:0 0 0 4px #e6f5ed}.history-item strong{color:#3c5b50;font-size:12px}.history-item p{margin:3px 0 0;color:#9aa7a1;font-size:11px}.plan-context{margin-top:18px}.context-summary,.context-empty{margin:0;color:#60776d;font-size:12px;line-height:1.75}.plan-context dl{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0 0}.plan-context dl>div{padding:10px;border:1px solid #e3ece7;border-radius:8px;background:#f8fbf9}.plan-context .context-wide{grid-column:1/-1}.plan-context dt{margin-bottom:4px;color:#8a9993;font-size:11px}.plan-context dd{margin:0;color:#345247;font-size:13px;line-height:1.55}@media(max-width:820px){.task-toolbar{align-items:stretch;flex-direction:column}.task-filters{flex-wrap:wrap}.task-filters .el-select{flex:1;min-width:130px}.task-table :deep(.el-table__cell:nth-child(2)),.task-table :deep(.el-table__cell:nth-child(4)){display:none}}@media(max-width:520px){.scope-tabs{width:100%;justify-content:space-between}.scope-tabs button{padding:0 8px;font-size:11px}.task-filters{display:grid;grid-template-columns:1fr 1fr}.task-filters .el-select,.task-filters :deep(.el-date-editor){width:100%}.completion-record dl,.task-facts,.plan-context dl{grid-template-columns:1fr}.completion-record .record-wide,.task-facts .fact-wide,.plan-context .context-wide{grid-column:auto}.drawer-commands{flex-direction:column}}
</style>
