<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getFarmManagementRecords, listFarmPlots, listFarms } from '@/api/production'
import { formatDateTime } from '@/utils/dataAdapters'

const loading = ref(false)
const farms = ref([])
const plots = ref([])
const records = ref([])
const productionYears = ref([])
const selectedRecord = ref(null)
const drawerOpen = ref(false)
const page = ref(1)
const pageSize = 20
const filters = reactive({ farmId: '', plotId: '', productionYear: null, recordType: '' })

const recordTypeOptions = [
  { value: '', label: '全部记录' },
  { value: 'plan_task', label: '计划任务' },
  { value: 'task_completion', label: '完成记录' },
  { value: 'historical_supplement', label: '历史阶段补录' },
  { value: 'temporary_task', label: '临时任务' },
  { value: 'change_order', label: '变更单' },
  { value: 'irrigation', label: '灌溉记录' },
  { value: 'milestone', label: '生产节点' },
]
const recordTypeMeta = {
  plan_task: { label: '计划任务', tone: 'plan' },
  ad_hoc_task: { label: '计划外农事', tone: 'field' },
  task_completion: { label: '完成记录', tone: 'done' },
  completion_correction: { label: '完成更正', tone: 'correction' },
  historical_supplement: { label: '历史阶段补录', tone: 'history' },
  temporary_task: { label: '临时任务', tone: 'temporary' },
  change_order: { label: '变更单', tone: 'change' },
  irrigation: { label: '灌溉记录', tone: 'water' },
  harvest_milestone: { label: '采收节点', tone: 'milestone' },
  cleanup_milestone: { label: '清园节点', tone: 'milestone' },
}
const sourceLabels = { template: '年度计划', planting: '定植安排', temporary: '临时任务', ad_hoc: '计划外农事', historical_supplement: '历史阶段补录' }
const statusLabels = { pending: '待执行', in_progress: '进行中', completed: '已完成', overdue: '已逾期', cancelled: '已取消', success: '成功', failed: '失败', timeout: '超时' }
const adjustmentLabels = { change_order: '变更单', temporary_task: '创建临时任务', completion: '登记完成', completion_correction: '追加更正', historical_supplement: '历史阶段补录', task_update: '任务调整' }

const filteredRecords = computed(() => {
  if (!filters.recordType) return records.value
  if (filters.recordType === 'milestone') return records.value.filter((item) => item.recordType.endsWith('_milestone'))
  if (filters.recordType === 'task_completion') return records.value.filter((item) => ['task_completion', 'completion_correction', 'ad_hoc_task'].includes(item.recordType))
  return records.value.filter((item) => item.recordType === filters.recordType)
})
const pagedRecords = computed(() => filteredRecords.value.slice((page.value - 1) * pageSize, page.value * pageSize))
const summary = computed(() => ({
  total: records.value.length,
  execution: records.value.filter((item) => ['task_completion', 'completion_correction', 'historical_supplement', 'ad_hoc_task'].includes(item.recordType)).length,
  adjustment: records.value.filter((item) => ['change_order', 'temporary_task'].includes(item.recordType)).length,
  irrigation: records.value.filter((item) => item.recordType === 'irrigation').length,
}))

function typeMeta(record) { return recordTypeMeta[record?.recordType] || { label: record?.recordType || '其他记录', tone: 'other' } }
function statusLabel(value) { return statusLabels[value] || value || '-' }
function statusTone(value) {
  if (['completed', 'success'].includes(value)) return 'success'
  if (['failed', 'timeout', 'overdue'].includes(value)) return 'danger'
  if (['pending', 'in_progress'].includes(value)) return 'warning'
  return 'info'
}
function productionYearText(year) { return `${year} 生产年度` }
function dateText(value) { return formatDateTime(value).slice(0, 16) }
function recordDateText(record) { return record?.id?.startsWith('task:') ? record.task?.scheduledDate || '-' : dateText(record?.occurredAt) }
function valueText(value) {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}
function changedFields(item) {
  const keys = [...new Set([...Object.keys(item.before || {}), ...Object.keys(item.after || {})])]
  return keys.filter((key) => key !== 'reason').map((key) => ({ key, before: item.before?.[key], after: item.after?.[key] }))
}
function fieldLabel(key) {
  return ({ scheduledDate: '计划日期', note: '备注', status: '状态', replacementTaskId: '替代任务', completionId: '完成记录' })[key] || key
}
function openDetail(record) {
  selectedRecord.value = record
  drawerOpen.value = true
}
function changeType() { page.value = 1 }

async function loadFarms() {
  try {
    farms.value = await listFarms()
    if (!farms.value.length) return
    filters.farmId = farms.value[0].id
    await changeFarm()
  } catch (error) { ElMessage.error(error.message || '农场列表加载失败') }
}
async function changeFarm() {
  filters.plotId = ''
  filters.productionYear = null
  try {
    const response = await listFarmPlots(filters.farmId)
    plots.value = response.items || []
    await loadRecords()
  } catch (error) { ElMessage.error(error.message || '管理记录加载失败') }
}
async function loadRecords() {
  if (!filters.farmId) return
  loading.value = true
  try {
    const response = await getFarmManagementRecords(filters.farmId, {
      plotId: filters.plotId || undefined,
      productionYear: filters.productionYear || undefined,
    })
    records.value = response.records || []
    productionYears.value = response.productionYears || []
    filters.productionYear = response.productionYear
    page.value = 1
  } catch (error) { ElMessage.error(error.message || '管理记录加载失败') }
  finally { loading.value = false }
}

onMounted(loadFarms)
</script>

<template>
  <div class="farmer-page records-page">
    <div class="page-head records-head">
      <div>
        <h1 class="page-title">管理记录</h1>
        <p class="page-subtitle">按生产年度追溯计划、执行、调整和灌溉档案</p>
      </div>
      <span class="readonly-mark"><el-icon><Lock /></el-icon>只读档案</span>
    </div>

    <section class="filter-band" aria-label="档案筛选">
      <label><span>农场</span><el-select v-model="filters.farmId" @change="changeFarm"><el-option v-for="farm in farms" :key="farm.id" :label="farm.name" :value="farm.id" /></el-select></label>
      <label><span>地块</span><el-select v-model="filters.plotId" @change="loadRecords"><el-option label="全部地块" value=""/><el-option v-for="plot in plots" :key="plot.id" :label="plot.name" :value="plot.id" /></el-select></label>
      <label><span>生产年度</span><el-select v-model="filters.productionYear" @change="loadRecords"><el-option v-for="year in productionYears" :key="year" :label="productionYearText(year)" :value="year" /></el-select></label>
      <label><span>记录类型</span><el-select v-model="filters.recordType" @change="changeType"><el-option v-for="item in recordTypeOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></label>
    </section>

    <section class="archive-summary" aria-label="档案统计">
      <div><span>全部档案</span><strong>{{ summary.total }}</strong></div>
      <div><span>执行与补录</span><strong>{{ summary.execution }}</strong></div>
      <div><span>调整记录</span><strong>{{ summary.adjustment }}</strong></div>
      <div><span>灌溉记录</span><strong>{{ summary.irrigation }}</strong></div>
    </section>

    <section class="records-panel" v-loading="loading">
      <header class="records-panel-head">
        <div><h2>生产档案时间线</h2><p>{{ filteredRecords.length }} 条记录，按发生时间倒序排列</p></div>
        <el-icon><Collection /></el-icon>
      </header>

      <el-table :data="pagedRecords" class="records-table" row-key="id" empty-text="当前筛选范围内暂无管理记录" @row-click="openDetail">
        <el-table-column label="计划/发生时间" width="154"><template #default="{ row }"><span class="record-time">{{ recordDateText(row) }}</span></template></el-table-column>
        <el-table-column label="类型" width="136"><template #default="{ row }"><span :class="['record-type', typeMeta(row).tone]"><i></i>{{ typeMeta(row).label }}</span></template></el-table-column>
        <el-table-column label="地块" min-width="128"><template #default="{ row }"><strong class="plot-name">{{ row.plotName }}</strong><small v-if="row.stageCode" class="stage-code">{{ row.stageCode }}</small></template></el-table-column>
        <el-table-column label="记录内容" min-width="220"><template #default="{ row }"><div class="record-copy"><strong>{{ row.title }}</strong><small>{{ row.note || row.result || '无补充说明' }}</small></div></template></el-table-column>
        <el-table-column label="执行人" min-width="110"><template #default="{ row }">{{ row.executorName || '-' }}</template></el-table-column>
        <el-table-column label="状态" width="96"><template #default="{ row }"><span :class="['record-status', statusTone(row.status)]">{{ statusLabel(row.status) }}</span></template></el-table-column>
        <el-table-column width="58" align="right"><template #default="{ row }"><el-tooltip content="查看详情" placement="top"><el-button text circle aria-label="查看详情" @click.stop="openDetail(row)"><el-icon><View /></el-icon></el-button></el-tooltip></template></el-table-column>
      </el-table>

      <div class="mobile-records">
        <button v-for="record in pagedRecords" :key="record.id" type="button" class="mobile-record" @click="openDetail(record)">
          <span :class="['record-type', typeMeta(record).tone]"><i></i>{{ typeMeta(record).label }}</span>
          <time>{{ recordDateText(record) }}</time>
          <strong>{{ record.title }}</strong>
          <small>{{ record.plotName }}<template v-if="record.stageCode"> · {{ record.stageCode }}</template></small>
          <el-icon><ArrowRight /></el-icon>
        </button>
        <el-empty v-if="!pagedRecords.length && !loading" :image-size="54" description="当前筛选范围内暂无管理记录" />
      </div>

      <footer v-if="filteredRecords.length > pageSize" class="records-pagination"><el-pagination v-model:current-page="page" background layout="prev, pager, next" :page-size="pageSize" :total="filteredRecords.length" /></footer>
    </section>

    <el-drawer v-model="drawerOpen" size="min(560px, 94vw)" :with-header="false" destroy-on-close>
      <template v-if="selectedRecord">
        <header class="detail-head">
          <div><span :class="['record-type', typeMeta(selectedRecord).tone]"><i></i>{{ typeMeta(selectedRecord).label }}</span><h2>{{ selectedRecord.title }}</h2><p>{{ recordDateText(selectedRecord) }}</p></div>
          <el-button text circle aria-label="关闭详情" @click="drawerOpen=false"><el-icon><Close /></el-icon></el-button>
        </header>
        <div class="detail-readonly"><el-icon><Lock /></el-icon><span>生产档案只读保存</span><span :class="['record-status', statusTone(selectedRecord.status)]">{{ statusLabel(selectedRecord.status) }}</span></div>

        <dl class="detail-facts">
          <div><dt>农场</dt><dd>{{ selectedRecord.farmName }}</dd></div>
          <div><dt>地块</dt><dd>{{ selectedRecord.plotName }}</dd></div>
          <div><dt>生产年度</dt><dd>{{ productionYearText(selectedRecord.productionYear) }}</dd></div>
          <div><dt>阶段</dt><dd>{{ selectedRecord.stageCode || '-' }}</dd></div>
          <div><dt>档案编号</dt><dd>{{ selectedRecord.referenceId }}</dd></div>
          <div><dt>执行人</dt><dd>{{ selectedRecord.executorName || '-' }}</dd></div>
        </dl>

        <section v-if="selectedRecord.result || selectedRecord.note" class="detail-section">
          <h3>记录结果</h3>
          <dl class="result-list"><div v-if="selectedRecord.result"><dt>执行结果</dt><dd>{{ statusLabel(selectedRecord.result) }}</dd></div><div v-if="selectedRecord.note"><dt>备注</dt><dd>{{ selectedRecord.note }}</dd></div></dl>
        </section>

        <section v-if="selectedRecord.task" class="detail-section">
          <h3>任务信息</h3>
          <dl class="detail-facts compact"><div><dt>任务来源</dt><dd>{{ sourceLabels[selectedRecord.task.source] || selectedRecord.task.source }}</dd></div><div><dt>任务类型</dt><dd>{{ selectedRecord.task.taskType }}</dd></div><div><dt>计划日期</dt><dd>{{ selectedRecord.task.scheduledDate }}</dd></div><div><dt>任务状态</dt><dd>{{ statusLabel(selectedRecord.task.status) }}</dd></div><div class="wide"><dt>任务备注</dt><dd>{{ selectedRecord.task.note || '-' }}</dd></div></dl>
        </section>

        <section v-if="selectedRecord.task?.completionHistory?.length" class="detail-section">
          <h3>完成与更正记录</h3>
          <ol class="history-chain">
            <li v-for="item in selectedRecord.task.completionHistory" :key="item.id">
              <i></i><div class="history-copy"><header><strong>{{ item.recordType === 'correction' ? '更正记录' : '原始完成记录' }}</strong><time>{{ dateText(item.createdAt) }}</time></header><dl><div><dt>实际执行</dt><dd>{{ dateText(item.executedAt) }}</dd></div><div><dt>执行人</dt><dd>{{ item.executorName }}</dd></div><div><dt>结果</dt><dd>{{ item.result }}</dd></div><div><dt>备注</dt><dd>{{ item.note || '-' }}</dd></div></dl></div>
            </li>
          </ol>
        </section>

        <section v-if="selectedRecord.task?.adjustments?.length" class="detail-section">
          <h3>任务变更历史</h3>
          <div class="adjustment-list">
            <article v-for="item in selectedRecord.task.adjustments" :key="item.id">
              <header><strong>{{ adjustmentLabels[item.type] || item.type }}</strong><time>{{ dateText(item.createdAt) }}</time></header>
              <p v-if="item.after?.reason">{{ item.after.reason }}</p>
              <dl v-if="changedFields(item).length"><div v-for="field in changedFields(item)" :key="field.key"><dt>{{ fieldLabel(field.key) }}</dt><dd><span>{{ valueText(field.before) }}</span><el-icon><Right /></el-icon><strong>{{ valueText(field.after) }}</strong></dd></div></dl>
            </article>
          </div>
        </section>

        <section v-if="selectedRecord.irrigation" class="detail-section">
          <h3>灌溉指令</h3>
          <dl class="detail-facts compact"><div><dt>设备</dt><dd>{{ selectedRecord.irrigation.deviceNo }}（{{ selectedRecord.irrigation.deviceId }}）</dd></div><div><dt>执行方式</dt><dd>{{ selectedRecord.irrigation.activationType === 'auto' ? '自动' : '手动' }}</dd></div><div><dt>请求时间</dt><dd>{{ dateText(selectedRecord.irrigation.requestedAt) }}</dd></div><div><dt>执行时间</dt><dd>{{ dateText(selectedRecord.irrigation.executedAt) }}</dd></div><div class="wide"><dt>计划时长</dt><dd>{{ selectedRecord.irrigation.durationMinutes ? `${selectedRecord.irrigation.durationMinutes} 分钟` : '-' }}</dd></div></dl>
        </section>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.records-head{align-items:center;margin-bottom:18px}.records-head .page-subtitle{margin-bottom:0}.readonly-mark{display:inline-flex;align-items:center;gap:7px;padding:8px 11px;border:1px solid #d6e5de;border-radius:7px;color:#557168;background:#f8fbf9;font-size:12px}.filter-band{display:grid;grid-template-columns:1.15fr 1fr 1fr 1fr;gap:12px;margin-bottom:14px;padding:15px 17px;border:1px solid #dce8e3;border-radius:8px;background:#fff}.filter-band label{display:grid;gap:6px;min-width:0}.filter-band label>span{color:#71847c;font-size:11px;font-weight:650}.filter-band :deep(.el-select){width:100%}.archive-summary{display:grid;grid-template-columns:repeat(4,1fr);margin-bottom:14px;border-block:1px solid #dfe9e4;background:rgba(255,255,255,.6)}.archive-summary>div{display:flex;align-items:baseline;justify-content:center;gap:9px;padding:13px;border-right:1px solid #e3ebe7}.archive-summary>div:last-child{border-right:0}.archive-summary span{color:#788b83;font-size:12px}.archive-summary strong{color:#245a46;font-size:22px}.records-panel{min-height:420px;border:1px solid #dce8e3;border-radius:8px;background:#fff;overflow:hidden}.records-panel-head{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e5ede9}.records-panel-head h2,.records-panel-head p{margin:0}.records-panel-head h2{color:#29483d;font-size:17px}.records-panel-head p{margin-top:4px;color:#8a9993;font-size:11px}.records-panel-head>.el-icon{color:#7aa18f;font-size:22px}.records-table{width:100%;cursor:pointer}.records-table :deep(th.el-table__cell){height:44px;color:#587067;background:#f4f8f6}.records-table :deep(td.el-table__cell){padding:12px 0}.record-time{color:#486359;font-variant-numeric:tabular-nums}.record-type{display:inline-flex;align-items:center;gap:7px;color:#527268;font-size:11px;font-weight:700;white-space:nowrap}.record-type i{width:8px;height:8px;border-radius:2px;background:#7c9b90}.record-type.done i{background:#2e976b}.record-type.correction i{background:#8b6fb1}.record-type.history i{background:#c57b30}.record-type.temporary i{background:#d39b2f}.record-type.change i{background:#ca625f}.record-type.water i{background:#398cbc}.record-type.milestone i{background:#7c7650}.record-type.field i{background:#699458}.plot-name,.stage-code{display:block}.plot-name{color:#315347;font-size:13px}.stage-code{margin-top:3px;color:#91a098;font-size:10px}.record-copy{display:grid;gap:4px}.record-copy strong{color:#2e4c41;font-size:13px}.record-copy small{max-width:360px;overflow:hidden;color:#87968f;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.record-status{display:inline-flex;align-items:center;justify-content:center;min-width:54px;padding:4px 7px;border-radius:6px;color:#5b746a;background:#eef3f1;font-size:10px}.record-status.success{color:#277c58;background:#e9f6ef}.record-status.warning{color:#a66d27;background:#fff2df}.record-status.danger{color:#b74f4f;background:#fbeaea}.records-pagination{display:flex;justify-content:flex-end;padding:14px 18px;border-top:1px solid #e7eeeb}.mobile-records{display:none}.detail-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;padding-bottom:18px;border-bottom:1px solid #e3ebe7}.detail-head h2{margin:11px 0 5px;color:#29483d;font-size:22px}.detail-head p{margin:0;color:#81918a;font-size:12px}.detail-readonly{display:flex;align-items:center;gap:7px;padding:13px 0;color:#698078;font-size:12px}.detail-readonly>.record-status{margin-left:auto}.detail-facts{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:0}.detail-facts>div{min-width:0;padding:11px 12px;border:1px solid #e3ebe7;border-radius:7px;background:#f8fbf9}.detail-facts dt,.result-list dt,.history-chain dt,.adjustment-list dt{margin-bottom:4px;color:#899991;font-size:10px}.detail-facts dd,.result-list dd,.history-chain dd,.adjustment-list dd{margin:0;color:#345347;font-size:12px;line-height:1.6;overflow-wrap:anywhere}.detail-section{margin-top:22px;padding-top:19px;border-top:1px solid #e4ece8}.detail-section h3{margin:0 0 13px;color:#315347;font-size:14px}.result-list{display:grid;gap:11px;margin:0}.result-list>div{padding-left:11px;border-left:3px solid #80ad96}.detail-facts.compact .wide{grid-column:1/-1}.history-chain{display:grid;gap:0;margin:0;padding:0;list-style:none}.history-chain li{position:relative;display:grid;grid-template-columns:15px 1fr;gap:9px;padding-bottom:16px}.history-chain li:not(:last-child)::before{position:absolute;top:14px;bottom:0;left:4px;width:1px;content:'';background:#dbe7e1}.history-chain li>i{position:relative;z-index:1;width:9px;height:9px;margin-top:5px;border-radius:50%;background:#32956a;box-shadow:0 0 0 4px #e5f3eb}.history-copy{padding:12px 13px;border:1px solid #e3ebe7;border-radius:7px}.history-copy header,.adjustment-list article>header{display:flex;align-items:center;justify-content:space-between;gap:10px}.history-copy header strong,.adjustment-list header strong{color:#315347;font-size:12px}.history-copy time,.adjustment-list time{color:#91a099;font-size:10px}.history-copy dl{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:12px 0 0}.adjustment-list{display:grid;gap:10px}.adjustment-list article{padding:13px;border:1px solid #e3ebe7;border-radius:7px}.adjustment-list article>p{margin:9px 0;color:#637a70;font-size:12px;line-height:1.6}.adjustment-list article>dl{display:grid;gap:8px;margin:11px 0 0}.adjustment-list article>dl>div{display:grid;grid-template-columns:80px 1fr;gap:8px;padding-top:8px;border-top:1px solid #edf2ef}.adjustment-list dd{display:flex;align-items:center;gap:7px}.adjustment-list dd span{color:#8a9993}.adjustment-list dd strong{font-weight:650}
@media(max-width:980px){.filter-band{grid-template-columns:1fr 1fr}.records-table :deep(.el-table__cell:nth-child(3)),.records-table :deep(.el-table__cell:nth-child(5)){display:none}}
@media(max-width:650px){.records-head{align-items:flex-start}.filter-band{grid-template-columns:1fr;padding:13px}.archive-summary{grid-template-columns:1fr 1fr}.archive-summary>div:nth-child(2){border-right:0}.archive-summary>div:nth-child(-n+2){border-bottom:1px solid #e3ebe7}.records-panel-head{padding:16px}.records-table{display:none}.mobile-records{display:grid}.mobile-record{position:relative;display:grid;grid-template-columns:1fr auto;gap:6px;width:100%;padding:15px 42px 15px 16px;border:0;border-bottom:1px solid #e8eeeb;color:inherit;background:#fff;text-align:left}.mobile-record time{color:#84948d;font-size:10px}.mobile-record>strong,.mobile-record>small{grid-column:1/-1}.mobile-record>strong{color:#2d4b40;font-size:14px}.mobile-record>small{color:#81918a;font-size:11px}.mobile-record>.el-icon{position:absolute;top:50%;right:15px;color:#82978d;transform:translateY(-50%)}.detail-facts,.history-copy dl{grid-template-columns:1fr}.detail-facts.compact .wide{grid-column:auto}.adjustment-list article>dl>div{grid-template-columns:1fr}.records-pagination{justify-content:center;overflow-x:auto}}
</style>
