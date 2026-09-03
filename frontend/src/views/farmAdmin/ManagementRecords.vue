<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getFarmProductionArchive, listFarmPlots, listFarmProductionArchives, listFarms } from '@/api/production'
import { formatDateTime } from '@/utils/dataAdapters'

const loading = ref(false)
const farms = ref([])
const plots = ref([])
const archives = ref([])
const archiveDetail = ref(null)
const selectedArchive = ref(null)
const selectedRecord = ref(null)
const drawerOpen = ref(false)
const filters = reactive({ farmId: '', plotId: '', recordType: '' })
const pages = reactive({ intervention: 1, execution: 1 })
const pageSize = 6

const recordTypeOptions = [
  { value: '', label: '全部记录' },
  { value: 'historical_supplement', label: '历史阶段补录' },
  { value: 'temporary_task', label: '临时任务' },
  { value: 'change_order', label: '任务变更单' },
  { value: 'task_completion', label: '任务完成记录' },
  { value: 'completion_correction', label: '完成更正记录' },
  { value: 'ad_hoc_task', label: '计划外农事' },
  { value: 'irrigation', label: '灌溉记录' },
  { value: 'harvest_milestone', label: '采收完成节点' },
  { value: 'cleanup_milestone', label: '清园完成节点' },
]
const recordTypeMeta = {
  historical_supplement: { label: '历史阶段补录', tone: 'history' },
  temporary_task: { label: '临时任务', tone: 'temporary' },
  change_order: { label: '任务变更单', tone: 'change' },
  task_completion: { label: '任务完成记录', tone: 'done' },
  completion_correction: { label: '完成更正记录', tone: 'correction' },
  ad_hoc_task: { label: '计划外农事', tone: 'field' },
  irrigation: { label: '灌溉记录', tone: 'water' },
  harvest_milestone: { label: '采收完成节点', tone: 'milestone' },
  cleanup_milestone: { label: '清园完成节点', tone: 'milestone' },
}
const sourceLabels = { template: '年度计划', planting: '定植安排', temporary: '临时任务', ad_hoc: '计划外农事', historical_supplement: '历史阶段补录' }
const statusLabels = { pending: '待执行', in_progress: '进行中', completed: '已完成', overdue: '已逾期', cancelled: '已取消', success: '成功', failed: '失败', timeout: '超时' }
const trackLabels = { young: '幼树轨道', fruiting: '结果树轨道' }

const interventionPage = computed(() => archiveDetail.value?.interventions || { items: [], total: 0 })
const executionPage = computed(() => archiveDetail.value?.executions || { items: [], total: 0 })

function typeMeta(record) { return recordTypeMeta[record?.recordType] || { label: record?.recordType || '其他记录', tone: 'other' } }
function statusLabel(value) { return statusLabels[value] || value || '-' }
function dateText(value) { return formatDateTime(value).slice(0, 16) }
function periodText(archive) { return `${archive.startsOn} 至 ${archive.endsOn}` }
function openRecord(record) { selectedRecord.value = record; drawerOpen.value = true }
function valueText(value) {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
function fieldLabel(key) { return ({ scheduledDate: '计划日期', note: '任务备注', status: '任务状态', replacementTaskId: '替代任务', reason: '变更原因' })[key] || key }
function changedFields(changeOrder) {
  const before = changeOrder?.before || {}
  const after = changeOrder?.after || {}
  return [...new Set([...Object.keys(before), ...Object.keys(after)])]
    .filter((key) => key !== 'reason' && key !== 'replacementTaskId')
    .map((key) => ({ key, before: before[key], after: after[key] }))
}

async function loadFarms() {
  try {
    farms.value = await listFarms()
    if (!farms.value.length) return
    filters.farmId = farms.value[0].id
    await changeFarm()
  } catch (error) { ElMessage.error(error.message || '农场列表加载失败') }
}
async function changeFarm() {
  selectedArchive.value = null
  archiveDetail.value = null
  filters.plotId = ''
  filters.recordType = ''
  loading.value = true
  try {
    const [archiveResponse, plotResponse] = await Promise.all([listFarmProductionArchives(filters.farmId), listFarmPlots(filters.farmId)])
    archives.value = archiveResponse.items || []
    plots.value = plotResponse.items || []
  } catch (error) { ElMessage.error(error.message || '生产档案加载失败') }
  finally { loading.value = false }
}
async function openArchive(archive) {
  selectedArchive.value = archive
  filters.plotId = ''
  filters.recordType = ''
  pages.intervention = 1
  pages.execution = 1
  await loadArchiveDetail()
}
async function loadArchiveDetail() {
  if (!selectedArchive.value) return
  loading.value = true
  try {
    archiveDetail.value = await getFarmProductionArchive(filters.farmId, selectedArchive.value.productionYear, {
      plotId: filters.plotId || undefined,
      recordType: filters.recordType || undefined,
      interventionPage: pages.intervention,
      interventionPageSize: pageSize,
      executionPage: pages.execution,
      executionPageSize: pageSize,
    })
  } catch (error) { ElMessage.error(error.message || '档案详情加载失败') }
  finally { loading.value = false }
}
function changeFilters() { pages.intervention = 1; pages.execution = 1; loadArchiveDetail() }
function changePage(kind, page) { pages[kind] = page; loadArchiveDetail() }
function backToArchives() { selectedArchive.value = null; archiveDetail.value = null; filters.plotId = ''; filters.recordType = '' }

onMounted(loadFarms)
</script>

<template>
  <div class="farmer-page archive-page" v-loading="loading">
    <div class="page-head archive-head">
      <div><h1 class="page-title">生产档案</h1><p class="page-subtitle">按生产年度查看管理干预、现场执行和关键生产节点</p></div>
      <span class="readonly-mark"><el-icon><Lock /></el-icon>只读档案</span>
    </div>

    <section v-if="!selectedArchive" class="archive-index">
      <div class="farm-filter">
        <label><span>农场</span><el-select v-model="filters.farmId" @change="changeFarm"><el-option v-for="farm in farms" :key="farm.id" :label="farm.name" :value="farm.id" /></el-select></label>
        <p>一个农场、一个生产年度对应一份生产档案</p>
      </div>
      <div class="archive-list">
        <button v-for="archive in archives" :key="archive.productionYear" type="button" class="archive-card" @click="openArchive(archive)">
          <header><div><span>生产年度</span><strong>{{ archive.productionYear }}</strong></div><el-icon><ArrowRight /></el-icon></header>
          <p class="archive-period">{{ periodText(archive) }}</p>
          <dl class="archive-facts"><div><dt>计划版本</dt><dd>{{ archive.templateName }} · V{{ archive.versionNo }}</dd></div><div><dt>树龄轨道</dt><dd>{{ trackLabels[archive.track] || archive.track }}</dd></div></dl>
          <div class="archive-counts"><span><b>{{ archive.interventionCount }}</b> 管理干预</span><span><b>{{ archive.executionCount }}</b> 执行记录</span></div>
          <div class="milestone-state"><span :class="{ done: archive.harvest.completed }"><i></i>采收{{ archive.harvest.completed ? '已完成' : '未记录' }}</span><span :class="{ done: archive.cleanup.completed }"><i></i>清园{{ archive.cleanup.completed ? '已完成' : '未记录' }}</span></div>
          <footer>最后更新 {{ dateText(archive.lastUpdatedAt) }}</footer>
        </button>
        <el-empty v-if="!archives.length && !loading" description="当前农场尚无年度生产档案" />
      </div>
    </section>

    <template v-else>
      <button type="button" class="back-link" @click="backToArchives"><el-icon><ArrowLeft /></el-icon>返回档案列表</button>
      <section class="archive-hero">
        <div class="archive-identity"><span>{{ selectedArchive.productionYear }} 生产年度</span><h2>{{ selectedArchive.templateName }} · V{{ selectedArchive.versionNo }}</h2><p>{{ periodText(selectedArchive) }} · {{ trackLabels[selectedArchive.track] || selectedArchive.track }}</p></div>
        <div class="hero-milestones"><span :class="{ done: selectedArchive.harvest.completed }"><small>采收</small><strong>{{ selectedArchive.harvest.completed ? dateText(selectedArchive.harvest.completedAt) : '未记录' }}</strong></span><span :class="{ done: selectedArchive.cleanup.completed }"><small>清园</small><strong>{{ selectedArchive.cleanup.completed ? dateText(selectedArchive.cleanup.completedAt) : '未记录' }}</strong></span></div>
      </section>
      <section class="detail-filter" aria-label="档案详情筛选">
        <label><span>地块</span><el-select v-model="filters.plotId" @change="changeFilters"><el-option label="全部地块" value=""/><el-option v-for="plot in plots" :key="plot.id" :label="plot.name" :value="plot.id" /></el-select></label>
        <label><span>记录类型</span><el-select v-model="filters.recordType" @change="changeFilters"><el-option v-for="item in recordTypeOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></label>
        <div class="filter-note"><el-icon><Lock /></el-icon><span>历史记录只读保留，更正以追加记录呈现</span></div>
      </section>

      <div class="record-columns">
        <section class="record-panel intervention-panel">
          <header><div><span class="section-kicker">计划侧</span><h2>管理干预与补录</h2><p>历史补录、临时任务和任务变更单</p></div><strong>{{ interventionPage.total }}</strong></header>
          <div class="record-list">
            <button v-for="record in interventionPage.items" :key="record.id" type="button" class="record-row" @click="openRecord(record)"><span :class="['record-type', typeMeta(record).tone]"><i></i>{{ typeMeta(record).label }}</span><time>{{ dateText(record.occurredAt) }}</time><strong>{{ record.title }}</strong><small>{{ record.plotName }}<template v-if="record.stageCode"> · {{ record.stageCode }}</template></small><p>{{ record.reason || record.note || record.result || '无补充说明' }}</p><el-icon><ArrowRight /></el-icon></button>
            <el-empty v-if="!interventionPage.items.length && !loading" :image-size="52" description="当前筛选下暂无管理干预记录" />
          </div>
          <footer v-if="interventionPage.total > pageSize"><el-pagination :current-page="pages.intervention" background layout="prev, pager, next" :page-size="pageSize" :total="interventionPage.total" @current-change="changePage('intervention', $event)" /></footer>
        </section>
        <section class="record-panel execution-panel">
          <header><div><span class="section-kicker">现场侧</span><h2>现场执行与生产节点</h2><p>完成、更正、计划外农事、灌溉及关键节点</p></div><strong>{{ executionPage.total }}</strong></header>
          <div class="record-list">
            <button v-for="record in executionPage.items" :key="record.id" type="button" class="record-row" @click="openRecord(record)"><span :class="['record-type', typeMeta(record).tone]"><i></i>{{ typeMeta(record).label }}</span><time>{{ dateText(record.occurredAt) }}</time><strong>{{ record.title }}</strong><small>{{ record.plotName }}<template v-if="record.stageCode"> · {{ record.stageCode }}</template></small><p>{{ record.result || record.note || '无补充说明' }}</p><el-icon><ArrowRight /></el-icon></button>
            <el-empty v-if="!executionPage.items.length && !loading" :image-size="52" description="当前筛选下暂无现场执行记录" />
          </div>
          <footer v-if="executionPage.total > pageSize"><el-pagination :current-page="pages.execution" background layout="prev, pager, next" :page-size="pageSize" :total="executionPage.total" @current-change="changePage('execution', $event)" /></footer>
        </section>
      </div>
    </template>

    <el-drawer v-model="drawerOpen" size="min(580px, 94vw)" :with-header="false" destroy-on-close>
      <template v-if="selectedRecord">
        <header class="drawer-head"><div><span :class="['record-type', typeMeta(selectedRecord).tone]"><i></i>{{ typeMeta(selectedRecord).label }}</span><h2>{{ selectedRecord.title }}</h2><p>{{ dateText(selectedRecord.occurredAt) }}</p></div><el-button text circle aria-label="关闭详情" @click="drawerOpen=false"><el-icon><Close /></el-icon></el-button></header>
        <div class="drawer-readonly"><el-icon><Lock /></el-icon><span>只读生产档案</span><el-tag size="small" effect="plain">{{ statusLabel(selectedRecord.status) }}</el-tag></div>
        <dl class="detail-grid"><div><dt>农场</dt><dd>{{ selectedRecord.farmName }}</dd></div><div><dt>地块</dt><dd>{{ selectedRecord.plotName }}</dd></div><div><dt>生产年度</dt><dd>{{ selectedRecord.productionYear }}</dd></div><div><dt>阶段</dt><dd>{{ selectedRecord.stageCode || '-' }}</dd></div><div><dt>档案编号</dt><dd>{{ selectedRecord.referenceId }}</dd></div><div><dt>执行/记录人</dt><dd>{{ selectedRecord.executorName || selectedRecord.recordedByName || '-' }}</dd></div></dl>
        <section v-if="selectedRecord.result || selectedRecord.note || selectedRecord.reason" class="drawer-section"><h3>记录内容</h3><dl class="result-list"><div v-if="selectedRecord.result"><dt>执行结果</dt><dd>{{ statusLabel(selectedRecord.result) }}</dd></div><div v-if="selectedRecord.reason"><dt>记录原因</dt><dd>{{ selectedRecord.reason }}</dd></div><div v-if="selectedRecord.note"><dt>备注</dt><dd>{{ selectedRecord.note }}</dd></div></dl></section>
        <section v-if="selectedRecord.task" class="drawer-section"><h3>关联任务</h3><dl class="detail-grid compact"><div><dt>任务编号</dt><dd>{{ selectedRecord.task.id }}</dd></div><div><dt>任务来源</dt><dd>{{ sourceLabels[selectedRecord.task.source] || selectedRecord.task.source }}</dd></div><div><dt>任务类型</dt><dd>{{ selectedRecord.task.taskType }}</dd></div><div><dt>计划日期</dt><dd>{{ selectedRecord.task.scheduledDate }}</dd></div><div class="wide"><dt>任务备注</dt><dd>{{ selectedRecord.task.note || '-' }}</dd></div></dl></section>
        <section v-if="selectedRecord.completion?.recordType === 'correction'" class="drawer-section"><h3>更正关系</h3><dl class="detail-grid compact"><div><dt>更正记录</dt><dd>{{ selectedRecord.completion.id }}</dd></div><div><dt>被更正记录</dt><dd>{{ selectedRecord.completion.correctsCompletionId }}</dd></div><div class="wide"><dt>更正原因</dt><dd>{{ selectedRecord.completion.reason || '-' }}</dd></div></dl></section>
        <section v-if="selectedRecord.changeOrder" class="drawer-section"><h3>任务替代关系</h3><dl class="detail-grid compact"><div><dt>原任务</dt><dd>{{ selectedRecord.changeOrder.originalTask.id }}</dd></div><div><dt>替代任务</dt><dd>{{ selectedRecord.changeOrder.replacementTask?.id || selectedRecord.changeOrder.after?.replacementTaskId || '-' }}</dd></div></dl><div class="change-list"><div v-for="field in changedFields(selectedRecord.changeOrder)" :key="field.key"><span>{{ fieldLabel(field.key) }}</span><p><del>{{ valueText(field.before) }}</del><el-icon><Right /></el-icon><strong>{{ valueText(field.after) }}</strong></p></div></div></section>
        <section v-if="selectedRecord.irrigation" class="drawer-section"><h3>灌溉记录</h3><dl class="detail-grid compact"><div><dt>设备</dt><dd>{{ selectedRecord.irrigation.deviceNo }}</dd></div><div><dt>执行方式</dt><dd>{{ selectedRecord.irrigation.activationType === 'auto' ? '自动' : '手动' }}</dd></div><div><dt>请求时间</dt><dd>{{ dateText(selectedRecord.irrigation.requestedAt) }}</dd></div><div><dt>执行时间</dt><dd>{{ dateText(selectedRecord.irrigation.executedAt) }}</dd></div><div class="wide"><dt>计划时长</dt><dd>{{ selectedRecord.irrigation.durationMinutes ? `${selectedRecord.irrigation.durationMinutes} 分钟` : '-' }}</dd></div></dl></section>
        <section v-if="selectedRecord.milestone" class="drawer-section"><h3>生产节点</h3><dl class="detail-grid compact"><div><dt>节点类型</dt><dd>{{ selectedRecord.milestone.type === 'harvest' ? '采收完成' : '清园完成' }}</dd></div><div><dt>完成时间</dt><dd>{{ dateText(selectedRecord.milestone.completedAt) }}</dd></div></dl></section>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.archive-head{align-items:center;margin-bottom:18px}.archive-head .page-subtitle{margin-bottom:0}.readonly-mark{display:inline-flex;align-items:center;gap:7px;padding:8px 11px;border:1px solid #d6e5de;border-radius:7px;color:#557168;background:#f8fbf9;font-size:12px}.farm-filter{display:flex;align-items:end;justify-content:space-between;gap:24px;padding:16px 18px;border-block:1px solid #dce8e3;background:#fff}.farm-filter label,.detail-filter label{display:grid;gap:6px}.farm-filter label>span,.detail-filter label>span{color:#71847c;font-size:11px;font-weight:650}.farm-filter .el-select{width:300px}.farm-filter p{margin:0;color:#81918a;font-size:12px}.archive-list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:18px}.archive-card{min-width:0;padding:19px;border:1px solid #dce7e2;border-radius:8px;color:inherit;background:#fff;text-align:left;transition:border-color .18s,box-shadow .18s,transform .18s}.archive-card:hover{border-color:#82ad99;box-shadow:0 8px 22px rgba(42,83,65,.09);transform:translateY(-2px)}.archive-card header{display:flex;align-items:center;justify-content:space-between}.archive-card header div{display:flex;align-items:baseline;gap:9px}.archive-card header span{color:#71847c;font-size:11px}.archive-card header strong{color:#245a46;font-size:27px}.archive-card header>.el-icon{color:#7f9b8e}.archive-period{margin:4px 0 17px;color:#8b9993;font-size:11px}.archive-facts{display:grid;gap:10px;margin:0;padding:14px 0;border-block:1px solid #e7eeea}.archive-facts>div{display:flex;justify-content:space-between;gap:12px}.archive-facts dt{color:#86978f;font-size:11px}.archive-facts dd{margin:0;color:#355448;font-size:12px;font-weight:650;text-align:right}.archive-counts{display:grid;grid-template-columns:1fr 1fr;margin:14px 0}.archive-counts span{color:#71847c;font-size:11px}.archive-counts b{margin-right:4px;color:#2b7357;font-size:18px}.milestone-state{display:flex;gap:14px}.milestone-state span{display:flex;align-items:center;gap:6px;color:#9a8271;font-size:10px}.milestone-state i{width:7px;height:7px;border-radius:50%;background:#c9b7aa}.milestone-state span.done{color:#33805e}.milestone-state span.done i{background:#389b70}.archive-card footer{margin-top:15px;color:#9aa6a1;font-size:10px}.back-link{display:inline-flex;align-items:center;gap:7px;margin-bottom:13px;padding:0;border:0;color:#46725f;background:none;font-size:12px;cursor:pointer}.archive-hero{display:flex;align-items:end;justify-content:space-between;gap:28px;padding:22px 25px;border-left:5px solid #df852e;background:#f7faf7}.archive-identity>span,.section-kicker{color:#b96d26;font-size:11px;font-weight:700}.archive-identity h2{margin:7px 0 5px;color:#29493d;font-size:23px}.archive-identity p{margin:0;color:#71847c;font-size:12px}.hero-milestones{display:flex;gap:28px}.hero-milestones span{display:grid;gap:5px;min-width:118px}.hero-milestones small{color:#8b9993;font-size:10px}.hero-milestones strong{color:#96765d;font-size:12px}.hero-milestones span.done strong{color:#2a7557}.detail-filter{display:grid;grid-template-columns:220px 240px 1fr;align-items:end;gap:12px;margin:15px 0;padding:14px 16px;border-block:1px solid #dfe9e4;background:#fff}.detail-filter .el-select{width:100%}.filter-note{display:flex;align-items:center;justify-content:flex-end;gap:7px;min-height:32px;color:#778b82;font-size:11px}.record-columns{display:grid;grid-template-columns:1fr 1fr;gap:16px}.record-panel{min-width:0;border:1px solid #dce7e2;border-radius:8px;background:#fff;overflow:hidden}.record-panel>header{display:flex;align-items:flex-start;justify-content:space-between;padding:18px;border-bottom:1px solid #e5ece8}.record-panel>header h2{margin:5px 0 3px;color:#2c4d40;font-size:17px}.record-panel>header p{margin:0;color:#8a9992;font-size:10px}.record-panel>header>strong{display:grid;place-items:center;min-width:34px;height:28px;border-radius:6px;color:#327758;background:#edf6f1;font-size:13px}.execution-panel .section-kicker{color:#367da5}.execution-panel>header>strong{color:#367da5;background:#edf5f9}.record-list{min-height:290px}.record-row{position:relative;display:grid;grid-template-columns:1fr auto;gap:5px;width:100%;min-height:116px;padding:15px 42px 14px 17px;border:0;border-bottom:1px solid #e8eeeb;color:inherit;background:#fff;text-align:left;cursor:pointer}.record-row:hover{background:#f8fbf9}.record-row time{color:#8b9993;font-size:10px}.record-row>strong,.record-row>small,.record-row>p{grid-column:1/-1}.record-row>strong{color:#2d4b40;font-size:14px}.record-row>small{color:#81918a;font-size:10px}.record-row>p{margin:2px 0 0;overflow:hidden;color:#63786e;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.record-row>.el-icon{position:absolute;top:50%;right:15px;color:#82978d;transform:translateY(-50%)}.record-type{display:inline-flex;align-items:center;gap:7px;color:#527268;font-size:10px;font-weight:700;white-space:nowrap}.record-type i{width:8px;height:8px;border-radius:2px;background:#7c9b90}.record-type.done i{background:#2e976b}.record-type.correction i{background:#8b6fb1}.record-type.history i{background:#c57b30}.record-type.temporary i{background:#d39b2f}.record-type.change i{background:#ca625f}.record-type.water i{background:#398cbc}.record-type.milestone i{background:#7c7650}.record-type.field i{background:#699458}.record-panel>footer{display:flex;justify-content:center;padding:13px;border-top:1px solid #e7eeeb}.drawer-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;padding-bottom:18px;border-bottom:1px solid #e3ebe7}.drawer-head h2{margin:10px 0 5px;color:#29483d;font-size:21px}.drawer-head p{margin:0;color:#81918a;font-size:12px}.drawer-readonly{display:flex;align-items:center;gap:7px;padding:13px 0;color:#698078;font-size:12px}.drawer-readonly .el-tag{margin-left:auto}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:0}.detail-grid>div{min-width:0;padding:11px 12px;border:1px solid #e3ebe7;border-radius:7px;background:#f8fbf9}.detail-grid dt,.result-list dt{margin-bottom:4px;color:#899991;font-size:10px}.detail-grid dd,.result-list dd{margin:0;color:#345347;font-size:12px;line-height:1.6;overflow-wrap:anywhere}.detail-grid .wide{grid-column:1/-1}.drawer-section{margin-top:22px;padding-top:19px;border-top:1px solid #e4ece8}.drawer-section h3{margin:0 0 13px;color:#315347;font-size:14px}.result-list{display:grid;gap:11px;margin:0}.result-list>div{padding-left:11px;border-left:3px solid #80ad96}.change-list{display:grid;gap:9px;margin-top:11px}.change-list>div{padding:11px 12px;border-left:3px solid #cb6862;background:#faf8f7}.change-list>div>span{color:#899991;font-size:10px}.change-list p{display:flex;align-items:center;gap:9px;margin:6px 0 0;color:#587067;font-size:11px}.change-list del{color:#9d7d7b}.change-list strong{color:#2f7156}
@media(max-width:1100px){.archive-list{grid-template-columns:repeat(2,minmax(0,1fr))}.detail-filter{grid-template-columns:1fr 1fr}.filter-note{grid-column:1/-1;justify-content:flex-start}}
@media(max-width:760px){.archive-head{align-items:flex-start}.farm-filter,.archive-hero{align-items:flex-start;flex-direction:column}.farm-filter .el-select{width:100%}.farm-filter label{width:100%}.archive-list,.record-columns,.detail-filter{grid-template-columns:1fr}.hero-milestones{width:100%;gap:12px}.hero-milestones span{min-width:0;flex:1}.filter-note{grid-column:auto}.record-panel{border-inline:0}.record-row{min-height:112px}.detail-grid{grid-template-columns:1fr}.detail-grid .wide{grid-column:auto}}
@media(max-width:460px){.archive-list{gap:10px}.archive-card{padding:16px}.archive-counts{gap:8px}.milestone-state{align-items:flex-start;flex-direction:column;gap:7px}.archive-hero{padding:19px}.hero-milestones{flex-direction:column}.detail-filter{padding-inline:0}.drawer-head h2{font-size:18px}}
</style>
