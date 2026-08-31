<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'
import { formatDateTime, parseDate } from '@/utils/dataAdapters'
import { getPlanChangeRequests } from '@/api/planChangeRequest'

const store = useFarmerStore()
const userStore = useUserStore()
const filters = reactive({ plotId: '', type: '', status: '' })
const dateRange = ref([])
const planRequests = ref([])
let refreshTimer = null
const requestStatus = { DRAFT: '待生成新计划', PENDING_REVIEW: '待管理员确认', APPROVED: '已确认新计划', ROLLED_BACK: '已退回原状态', CANCELLED: '已取消' }
const requestRows = computed(() => planRequests.value.map((item) => ({
  ...item, alertId: item.requestId, type: '计划变更申请', typeCode: 'plan_change_request',
  plotName: item.plotName, reason: item.requestReason, status: requestStatus[item.status] || item.status,
  statusCode: item.status, occurTime: formatDateTime(item.submittedAt || item.createdAt),
})))
const alertTime = (value) => parseDate(value)?.getTime() || 0
const inDateRange = (item) => dateRange.value?.length !== 2 || (alertTime(item.occurTime) >= dateRange.value[0].getTime() && alertTime(item.occurTime) <= dateRange.value[1].getTime())
const allRows = computed(() => [...requestRows.value, ...store.visibleAlerts])
const filtered = computed(() => allRows.value.filter((item) => (!filters.plotId || item.plotId === filters.plotId) && (!filters.type || item.type === filters.type) && (!filters.status || item.status === filters.status) && inDateRange(item)))

function metricText(value) {
  if (value === null || value === undefined || value === '' || value === '-') return '—'
  const number = Number(value)
  return Number.isFinite(number) ? number.toFixed(2).replace(/\.00$/, '') : value
}

function alertReason(item) {
  if (item.typeCode === 'plan_change_request') return item.reason || '未填写申请原因'
  if (item.typeCode === 'low_moisture' || item.type === '湿度过低') {
    return `实测湿度 ${metricText(item.value)}%，告警阈值 ${metricText(item.threshold)}%`
  }
  if (item.typeCode === 'device_fault' || item.typeCode === 'device_offline') {
    return `设备编号：${item.deviceNo || item.deviceId || '未关联设备'}`
  }
  if (item.typeCode === 'irrigation_failed') return '—'
  return item.reason || '—'
}
async function refreshPageAlerts() {
  await store.refreshAlerts()
}

onMounted(async () => {
  const [, requests] = await Promise.all([
    refreshPageAlerts(),
    getPlanChangeRequests(),
  ])
  planRequests.value = requests
  refreshTimer = window.setInterval(() => {
    refreshPageAlerts().catch(() => {})
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})

async function confirmAlert(item) {
  await ElMessageBox.confirm(`确认已知晓 ${item.plotName} 的“${item.type}”告警？`, '确认告警', { type: 'warning' })
  await store.acknowledge(item.alertId)
  ElMessage.success('告警已确认')
}

function resetFilters() { Object.assign(filters, { plotId: '', type: '', status: '' }); dateRange.value = [] }
</script>

<template>
  <div class="farmer-page">
    <div class="page-head"><div><h1 class="page-title">告警中心</h1><p class="page-subtitle">查看普通告警和计划变更结果；新计划生成后无需农户再次操作。</p></div><span class="status-pill danger">{{ store.unhandledCount }} 项待处理</span></div>
    <section class="content-panel">
      <div class="filter-bar">
        <el-select v-model="filters.plotId" clearable placeholder="全部地块"><el-option v-for="item in store.accessiblePlots" :key="item.plotId" :label="item.plotName" :value="item.plotId" /></el-select>
        <el-select v-model="filters.type" clearable placeholder="告警类型"><el-option v-for="item in ['计划变更申请','湿度过低','设备故障','设备离线','灌溉失败']" :key="item" :label="item" :value="item" /></el-select>
        <el-select v-model="filters.status" clearable placeholder="处理结果"><el-option v-for="item in ['未处理','处理中','已处理','待生成新计划','待管理员确认','已确认新计划','已退回原状态']" :key="item" :label="item" :value="item" /></el-select>
        <el-date-picker v-model="dateRange" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" clearable />
        <el-button @click="resetFilters">重置</el-button>
      </div>
      <el-table :data="filtered" class="compact-table" stripe>
        <el-table-column prop="occurTime" label="发生时间" min-width="165" />
        <el-table-column prop="plotName" label="地块" min-width="110" />
        <el-table-column prop="type" label="类型" min-width="135"><template #default="scope"><span class="status-pill warning">{{ scope.row.type }}</span></template></el-table-column>
        <el-table-column label="原因 / 建议" min-width="300" show-overflow-tooltip><template #default="scope">{{ alertReason(scope.row) }}</template></el-table-column>
        <el-table-column prop="status" label="状态" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === '未处理' ? 'danger' : '']">{{ scope.row.status }}</span></template></el-table-column>
        <el-table-column label="处理" width="130" fixed="right"><template #default="scope"><div class="action-row">
          <el-button v-if="scope.row.typeCode !== 'plan_change_request' && scope.row.status === '未处理' && userStore.can('alert','modify')" size="small" type="primary" plain @click="confirmAlert(scope.row)">确认告警</el-button>
          <span v-else>—</span>
        </div></template></el-table-column>
      </el-table>
      <el-empty v-if="!filtered.length" description="暂无符合条件的告警" />
    </section>
  </div>
</template>

<style scoped>.filter-bar{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:18px}.filter-bar .el-select{width:170px}.filter-bar :deep(.el-date-editor){width:360px}.action-row{display:flex;gap:8px;align-items:center;white-space:nowrap}.action-row :deep(.el-button){margin:0}@media(max-width:760px){.filter-bar :deep(.el-date-editor){width:100%}}</style>
