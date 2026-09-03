<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { usePlatformStore } from '@/stores/platform'

const store = usePlatformStore()
const route = useRoute()
const router = useRouter()
const keyword = ref('')
const statusFilter = ref('all')
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({ farmId: '', name: '', province: '重庆市', city: '奉节县', address: '', areaMu: null, managerName: '', note: '', status: 'active' })
const rules = {
  name: [{ required: true, message: '请输入橙园名称', trigger: 'blur' }],
  province: [{ required: true, message: '请输入所在省级行政区', trigger: 'blur' }],
  city: [{ required: true, message: '请输入所在市或区县', trigger: 'blur' }],
  areaMu: [{ validator: (_rule, value, callback) => value === null || value === '' || Number(value) >= 0 ? callback() : callback(new Error('面积不能小于 0')), trigger: 'change' }],
}

const plotRows = ref([])
const plotTotal = ref(0)
const plotPage = ref(1)
const plotPageSize = 10
const plotKeyword = ref('')
const plotStatusFilter = ref('all')
const plotLoading = ref(false)
const plotDialogVisible = ref(false)
const plotSaving = ref(false)
const plotFormRef = ref()
const plotForm = reactive({ plotId: '', farmId: '', code: '', name: '', areaMu: null, location: '', irrigationMethod: null, status: 'active' })
const globalPlotDialogVisible = ref(false)
const globalPlotKeyword = ref('')
const globalPlotRows = ref([])
const globalPlotLoading = ref(false)
const plotRules = {
  code: [{ required: true, message: '请输入地块编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入地块名称', trigger: 'blur' }],
  areaMu: [{ validator: (_rule, value, callback) => value === null || value === '' || Number(value) >= 0 ? callback() : callback(new Error('面积不能小于 0')), trigger: 'change' }],
}
const irrigationLabels = { drip: '滴灌', sprinkler: '喷灌', flood: '漫灌', manual: '人工灌溉', other: '其他' }

const selectedFarmId = computed(() => String(route.query.farmId || ''))
const selectedFarm = computed(() => store.farms.find((farm) => farm.farmId === selectedFarmId.value))
const isPlotView = computed(() => Boolean(selectedFarmId.value))
const farms = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return store.farms.filter((farm) => {
    const matchesStatus = statusFilter.value === 'all' || farm.status === statusFilter.value
    const searchable = `${farm.farmId} ${farm.name} ${farm.province} ${farm.city} ${farm.address} ${farm.managerName}`.toLowerCase()
    return matchesStatus && (!query || searchable.includes(query))
  })
})

function resetForm() {
  Object.assign(form, { farmId: '', name: '', province: '重庆市', city: '奉节县', address: '', areaMu: null, managerName: '', note: '', status: 'active' })
  nextTick(() => formRef.value?.clearValidate())
}

function addFarm() { resetForm(); dialogVisible.value = true }
function editFarm(row) {
  Object.assign(form, { farmId: row.farmId, name: row.name || '', province: row.province || '', city: row.city || '', address: row.address || '', areaMu: row.areaMu ?? null, managerName: row.managerName || '', note: row.note || '', status: row.status || 'active' })
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

async function saveFarm() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await store.saveFarm({ ...form })
    dialogVisible.value = false
    ElMessage.success(form.farmId ? '橙园档案已更新' : '橙园档案已创建')
  } catch (error) { ElMessage.error(error.message || '橙园档案保存失败') }
  finally { saving.value = false }
}

async function toggleFarm(row) {
  const deactivating = row.status === 'active'
  const action = deactivating ? '停用' : '恢复'
  try {
    await ElMessageBox.confirm(deactivating ? `停用只会改变 ${row.name} 的档案状态，所属地块、授权关系和历史记录均会保留，不会被删除；恢复前不应继续新增授权、设备绑定或生产计划。确认继续？` : `确认恢复 ${row.name}？恢复后可继续用于后续业务配置。`, `${action}橙园`, { type: deactivating ? 'warning' : 'success', confirmButtonText: `确认${action}`, cancelButtonText: '取消' })
    await store.toggleFarm(row.farmId)
    ElMessage.success(`橙园已${action}`)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message || `${action}橙园失败`)
  }
}

async function refreshFarms() {
  try { await store.loadData(true); ElMessage.success('橙园档案已刷新') }
  catch (error) { ElMessage.error(error.message || '橙园档案刷新失败') }
}

function openPlots(farm) { router.push({ name: 'admin-archives', query: { farmId: farm.farmId } }) }
function returnToFarms() { router.push({ name: 'admin-archives' }) }

async function searchGlobalPlots() {
  globalPlotLoading.value = true
  try {
    const result = await store.listFarmPlots({ farmId: '', page: 1, pageSize: 100, keyword: globalPlotKeyword.value.trim(), status: '' })
    globalPlotRows.value = result.items
  } catch (error) { ElMessage.error(error.message || '全平台地块搜索失败') }
  finally { globalPlotLoading.value = false }
}
function openGlobalPlotSearch() {
  globalPlotKeyword.value = ''
  globalPlotDialogVisible.value = true
  searchGlobalPlots()
}
function farmName(farmId) { return store.farms.find((farm) => farm.farmId === farmId)?.name || farmId }

async function loadPlots() {
  if (!selectedFarmId.value) return
  plotLoading.value = true
  try {
    const result = await store.listFarmPlots({ farmId: selectedFarmId.value, page: plotPage.value, pageSize: plotPageSize, keyword: plotKeyword.value.trim(), status: plotStatusFilter.value === 'all' ? '' : plotStatusFilter.value })
    plotRows.value = result.items
    plotTotal.value = result.total
  } catch (error) { ElMessage.error(error.message || '地块档案加载失败') }
  finally { plotLoading.value = false }
}

function searchPlots() { plotPage.value = 1; loadPlots() }
function changePlotPage(page) { plotPage.value = page; loadPlots() }
function resetPlotForm() {
  Object.assign(plotForm, { plotId: '', farmId: selectedFarmId.value, code: '', name: '', areaMu: null, location: '', irrigationMethod: null, status: 'active' })
  nextTick(() => plotFormRef.value?.clearValidate())
}
function addPlot() { resetPlotForm(); plotDialogVisible.value = true }
function editPlot(row) {
  Object.assign(plotForm, { plotId: row.plotNo, farmId: row.farmId, code: row.code || '', name: row.name || '', areaMu: row.areaMu ?? null, location: row.location || '', irrigationMethod: row.irrigationMethod || null, status: row.status || 'active' })
  plotDialogVisible.value = true
  nextTick(() => plotFormRef.value?.clearValidate())
}

async function savePlot() {
  const valid = await plotFormRef.value?.validate().catch(() => false)
  if (!valid) return
  plotSaving.value = true
  try {
    await store.savePlot({ ...plotForm })
    plotDialogVisible.value = false
    await loadPlots()
    ElMessage.success(plotForm.plotId ? '地块档案已更新' : '地块档案已创建')
  } catch (error) {
    ElMessage.error(error.message === 'PLOT_CODE_EXISTS' ? '地块编号已存在，请更换后重试' : error.message || '地块档案保存失败')
  } finally { plotSaving.value = false }
}

async function togglePlot(row) {
  const deactivating = row.status === 'active'
  const action = deactivating ? '停用' : '恢复'
  try {
    await ElMessageBox.confirm(deactivating ? `确认停用地块 ${row.name}？停用后不再参与新的生产计划。` : `确认恢复地块 ${row.name}？`, `${action}地块`, { type: deactivating ? 'warning' : 'success', confirmButtonText: `确认${action}`, cancelButtonText: '取消' })
    await store.togglePlot(row)
    await loadPlots()
    ElMessage.success(`地块已${action}`)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message || `${action}地块失败`)
  }
}

function irrigationStatus(row) {
  const devices = store.devices.filter((device) => (device.plotNo || device.plotId) === row.plotNo && device.type === '灌溉设备')
  if (!devices.length) return { label: '未绑定', tone: 'info' }
  if (devices.some((device) => device.switchState === 'on' || device.latestValue === '运行中')) return { label: '灌溉中', tone: 'success' }
  if (devices.every((device) => device.status === '离线' || device.status === '异常')) return { label: '离线', tone: 'danger' }
  return { label: '待机', tone: '' }
}

function formatArea(value) {
  if (value === null || value === undefined || value === '') return '未填写'
  return `${Number(value).toLocaleString('zh-CN', { maximumFractionDigits: 2 })} 亩`
}
function formatTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').replace(/\.\d+Z?$/, '').replace(/Z$/, '')
}

watch(selectedFarmId, (farmId) => {
  if (!farmId) return
  plotPage.value = 1
  plotKeyword.value = ''
  plotStatusFilter.value = 'all'
  loadPlots()
}, { immediate: true })
</script>

<template>
  <div class="farmer-page archive-page">
    <div v-if="!isPlotView" class="page-head">
      <div><h1 class="page-title">基础档案</h1><p class="page-subtitle">统一维护公司旗下橙园的基础信息与启用状态。</p></div>
      <div class="page-actions"><el-button @click="openGlobalPlotSearch"><el-icon><Search /></el-icon>全平台地块搜索</el-button><el-button type="primary" @click="addFarm"><el-icon><Plus /></el-icon>新增橙园</el-button></div>
    </div>
    <div v-else class="page-head detail-head">
      <div class="detail-heading">
        <el-tooltip content="返回橙园列表" placement="top"><el-button circle aria-label="返回橙园列表" @click="returnToFarms"><el-icon><ArrowLeft /></el-icon></el-button></el-tooltip>
        <div><h1 class="page-title">{{ selectedFarm?.name || selectedFarmId }}</h1><p class="page-subtitle">基础档案 / 橙园档案 / 地块档案</p></div>
      </div>
      <el-tooltip :disabled="selectedFarm?.status !== 'inactive'" content="已停用橙园不能新增地块" placement="top"><span><el-button type="primary" :disabled="selectedFarm?.status === 'inactive'" @click="addPlot"><el-icon><Plus /></el-icon>新增地块</el-button></span></el-tooltip>
    </div>

    <section v-if="!isPlotView" class="content-panel archive-panel">
      <div class="section-head">
        <div><h3>橙园列表</h3><p>共 {{ store.farms.length }} 个橙园，当前显示 {{ farms.length }} 个</p></div>
        <div class="table-toolbar">
          <el-select v-model="statusFilter" aria-label="按状态筛选" class="status-filter"><el-option label="全部状态" value="all" /><el-option label="启用" value="active" /><el-option label="已停用" value="inactive" /></el-select>
          <el-input v-model="keyword" clearable placeholder="搜索名称、编号、地址或负责人"><template #prefix><el-icon><Search /></el-icon></template></el-input>
          <el-tooltip content="刷新档案" placement="top"><el-button :loading="store.loading" aria-label="刷新档案" @click="refreshFarms"><el-icon><RefreshRight /></el-icon></el-button></el-tooltip>
        </div>
      </div>
      <el-table v-loading="store.loading" :data="farms" class="compact-table" row-key="farmId">
        <el-table-column prop="farmId" label="橙园编号" width="110" />
        <el-table-column prop="name" label="橙园名称" min-width="170"><template #default="scope"><el-button link type="primary" class="record-link" @click="openPlots(scope.row)">{{ scope.row.name }}</el-button></template></el-table-column>
        <el-table-column label="所在地区" min-width="150"><template #default="scope">{{ [scope.row.province, scope.row.city].filter(Boolean).join(' · ') || '-' }}</template></el-table-column>
        <el-table-column prop="address" label="详细地址" min-width="210" show-overflow-tooltip><template #default="scope">{{ scope.row.address || '-' }}</template></el-table-column>
        <el-table-column label="面积" width="110" align="right"><template #default="scope">{{ formatArea(scope.row.areaMu) }}</template></el-table-column>
        <el-table-column prop="managerName" label="负责人" width="110"><template #default="scope">{{ scope.row.managerName || '未填写' }}</template></el-table-column>
        <el-table-column label="状态" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === 'inactive' ? 'info' : '']">{{ scope.row.status === 'active' ? '启用' : '已停用' }}</span></template></el-table-column>
        <el-table-column label="更新时间" width="170"><template #default="scope">{{ formatTime(scope.row.updatedAt) }}</template></el-table-column>
        <el-table-column label="操作" fixed="right" width="235" align="right"><template #default="scope"><el-button link type="primary" @click="openPlots(scope.row)"><el-icon><LocationInformation /></el-icon>地块档案</el-button><el-button link type="primary" @click="editFarm(scope.row)">编辑</el-button><el-button link :type="scope.row.status === 'active' ? 'danger' : 'success'" @click="toggleFarm(scope.row)">{{ scope.row.status === 'active' ? '停用' : '恢复' }}</el-button></template></el-table-column>
        <template #empty><el-empty description="暂无符合条件的橙园档案" :image-size="72" /></template>
      </el-table>
    </section>

    <section v-else class="content-panel archive-panel">
      <div class="section-head">
        <div><h3>地块列表</h3><p>{{ selectedFarmId }} · 共 {{ plotTotal }} 个地块</p></div>
        <div class="table-toolbar">
          <el-select v-model="plotStatusFilter" aria-label="按地块状态筛选" class="status-filter" @change="searchPlots"><el-option label="全部状态" value="all" /><el-option label="启用" value="active" /><el-option label="已停用" value="inactive" /></el-select>
          <el-input v-model="plotKeyword" clearable placeholder="搜索地块编号或名称" @keyup.enter="searchPlots" @clear="searchPlots"><template #prefix><el-icon><Search /></el-icon></template></el-input>
          <el-tooltip content="查询地块" placement="top"><el-button aria-label="查询地块" @click="searchPlots"><el-icon><Search /></el-icon></el-button></el-tooltip>
          <el-tooltip content="刷新地块" placement="top"><el-button :loading="plotLoading" aria-label="刷新地块" @click="loadPlots"><el-icon><RefreshRight /></el-icon></el-button></el-tooltip>
        </div>
      </div>
      <el-table v-loading="plotLoading" :data="plotRows" class="compact-table" row-key="plotNo">
        <el-table-column prop="code" label="地块编号" width="130" /><el-table-column prop="name" label="地块名称" min-width="170"><template #default="scope"><strong class="record-name">{{ scope.row.name }}</strong></template></el-table-column>
        <el-table-column label="面积" width="110" align="right"><template #default="scope">{{ formatArea(scope.row.areaMu) }}</template></el-table-column>
        <el-table-column prop="location" label="位置说明" min-width="220" show-overflow-tooltip><template #default="scope">{{ scope.row.location || '未填写' }}</template></el-table-column>
        <el-table-column label="灌溉状态" width="120"><template #default="scope"><span :class="['status-pill', irrigationStatus(scope.row).tone]">{{ irrigationStatus(scope.row).label }}</span></template></el-table-column>
        <el-table-column label="状态" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === 'inactive' ? 'info' : '']">{{ scope.row.status === 'active' ? '启用' : '已停用' }}</span></template></el-table-column>
        <el-table-column label="更新时间" width="170"><template #default="scope">{{ formatTime(scope.row.updatedAt) }}</template></el-table-column>
        <el-table-column label="操作" fixed="right" width="150" align="right"><template #default="scope"><el-button link type="primary" @click="editPlot(scope.row)"><el-icon><EditPen /></el-icon>编辑</el-button><el-button link :type="scope.row.status === 'active' ? 'danger' : 'success'" @click="togglePlot(scope.row)">{{ scope.row.status === 'active' ? '停用' : '恢复' }}</el-button></template></el-table-column>
        <template #empty><el-empty description="该橙园暂无符合条件的地块" :image-size="72" /></template>
      </el-table>
      <div v-if="plotTotal > plotPageSize" class="pagination"><el-pagination background layout="prev, pager, next" :current-page="plotPage" :page-size="plotPageSize" :total="plotTotal" @current-change="changePlotPage" /></div>
    </section>

    <el-dialog v-model="dialogVisible" :title="form.farmId ? '编辑橙园档案' : '新增橙园档案'" width="min(640px, calc(100vw - 32px))" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top"><div class="form-grid"><el-form-item label="橙园名称" prop="name"><el-input v-model="form.name" maxlength="100" show-word-limit placeholder="请输入橙园名称" /></el-form-item><el-form-item label="负责人" prop="managerName"><el-input v-model="form.managerName" maxlength="50" placeholder="请输入负责人姓名" /></el-form-item><el-form-item label="所在省级行政区" prop="province"><el-input v-model="form.province" maxlength="50" placeholder="例如：重庆市" /></el-form-item><el-form-item label="所在市或区县" prop="city"><el-input v-model="form.city" maxlength="50" placeholder="例如：奉节县" /></el-form-item><el-form-item class="full-row" label="详细地址" prop="address"><el-input v-model="form.address" maxlength="255" placeholder="请输入乡镇、村及具体位置" /></el-form-item><el-form-item label="面积（亩）" prop="areaMu"><el-input-number v-model="form.areaMu" :min="0" :precision="2" :step="1" controls-position="right" /></el-form-item><el-form-item v-if="form.farmId" label="档案状态"><el-switch v-model="form.status" active-value="active" inactive-value="inactive" active-text="启用" inactive-text="停用" /></el-form-item><el-form-item class="full-row" label="备注" prop="note"><el-input v-model="form.note" type="textarea" :rows="3" maxlength="500" show-word-limit resize="none" placeholder="补充橙园档案说明（选填）" /></el-form-item></div></el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveFarm">保存档案</el-button></template>
    </el-dialog>

    <el-dialog v-model="plotDialogVisible" :title="plotForm.plotId ? '编辑地块档案' : '新增地块档案'" width="min(620px, calc(100vw - 32px))" destroy-on-close>
      <el-form ref="plotFormRef" :model="plotForm" :rules="plotRules" label-position="top"><div class="form-grid"><el-form-item class="full-row" label="所属橙园"><el-input :model-value="selectedFarm?.name || selectedFarmId" disabled /></el-form-item><el-form-item label="地块编号" prop="code"><el-input v-model="plotForm.code" maxlength="50" placeholder="全平台唯一，例如 FJ-001" /></el-form-item><el-form-item label="地块名称" prop="name"><el-input v-model="plotForm.name" maxlength="100" placeholder="请输入地块名称" /></el-form-item><el-form-item label="面积（亩）" prop="areaMu"><el-input-number v-model="plotForm.areaMu" :min="0" :precision="2" :step="1" controls-position="right" /></el-form-item><el-form-item label="灌溉方式"><el-select v-model="plotForm.irrigationMethod" clearable placeholder="请选择"><el-option v-for="(label, value) in irrigationLabels" :key="value" :label="label" :value="value" /></el-select></el-form-item><el-form-item class="full-row" label="位置说明"><el-input v-model="plotForm.location" maxlength="255" placeholder="请输入地块所在位置" /></el-form-item><el-form-item v-if="plotForm.plotId" label="档案状态"><el-switch v-model="plotForm.status" active-value="active" inactive-value="inactive" active-text="启用" inactive-text="停用" /></el-form-item></div></el-form>
      <template #footer><el-button @click="plotDialogVisible = false">取消</el-button><el-button type="primary" :loading="plotSaving" @click="savePlot">保存档案</el-button></template>
    </el-dialog>

    <el-dialog v-model="globalPlotDialogVisible" title="全平台地块搜索" width="min(820px, calc(100vw - 32px))" destroy-on-close>
      <div class="global-search-toolbar"><el-input v-model="globalPlotKeyword" clearable placeholder="输入地块编号或名称" @keyup.enter="searchGlobalPlots" @clear="searchGlobalPlots"><template #prefix><el-icon><Search /></el-icon></template></el-input><el-button type="primary" :loading="globalPlotLoading" @click="searchGlobalPlots"><el-icon><Search /></el-icon>搜索</el-button></div>
      <p class="global-search-note">搜索范围覆盖全部橙园；新增或修改时，系统仍会在保存前校验地块编号全平台唯一。</p>
      <el-table v-loading="globalPlotLoading" :data="globalPlotRows" max-height="430" row-key="plotNo"><el-table-column prop="code" label="地块编号" width="140" /><el-table-column prop="name" label="地块名称" min-width="180" /><el-table-column label="所属橙园" min-width="190"><template #default="scope">{{ farmName(scope.row.farmId) }}</template></el-table-column><el-table-column label="状态" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === 'inactive' ? 'info' : '']">{{ scope.row.status === 'active' ? '启用' : '已停用' }}</span></template></el-table-column><template #empty><el-empty description="未找到匹配的地块" :image-size="64" /></template></el-table>
    </el-dialog>
  </div>
</template>

<style scoped>
.archive-page{min-width:0}.archive-page>.page-head{align-items:center;margin-bottom:18px}.archive-page .page-subtitle{margin-bottom:0}.detail-heading{display:flex;align-items:center;gap:14px}.archive-panel{padding:20px 0 0;overflow:hidden}.archive-panel .section-head{align-items:center;padding:0 20px}.table-toolbar{display:flex;align-items:center;gap:10px}.table-toolbar .status-filter{width:126px}.table-toolbar .el-input{width:280px}.record-link{height:auto;padding:0!important;font-weight:700}.record-name{color:#29473d;font-weight:700}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}.form-grid .full-row{grid-column:1/-1}.form-grid .el-input-number,.form-grid .el-select{width:100%}.compact-table :deep(.el-table__cell:first-child){padding-left:20px}.compact-table :deep(.el-table__cell:last-child){padding-right:20px}.pagination{display:flex;justify-content:flex-end;padding:18px 20px}.global-search-toolbar{display:flex;gap:10px}.global-search-note{margin:10px 0 16px;color:#71807b;font-size:12px;line-height:1.6}@media(max-width:800px){.archive-page>.page-head{align-items:flex-start}.archive-page>.page-head>.page-actions{width:100%}.archive-page>.page-head>.page-actions .el-button{flex:1}.detail-heading{align-items:flex-start}.archive-panel .section-head{align-items:flex-start;flex-direction:column}.table-toolbar{width:100%;flex-wrap:wrap}.table-toolbar .status-filter,.table-toolbar .el-input{width:100%}.form-grid{grid-template-columns:1fr}.form-grid .full-row{grid-column:auto}.pagination{justify-content:center}.global-search-toolbar{flex-direction:column}}
</style>
