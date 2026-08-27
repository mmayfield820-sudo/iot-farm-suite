<template>
  <div class="farmer-page alerts-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">告警日志</h1>
        <p class="page-subtitle">跟踪农场异常、处理进度与设备恢复情况</p>
      </div>
      <div class="alert-summary"><strong>{{ unhandledCount }}</strong><span>项待处理</span></div>
    </div>
    <el-card class="alerts-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="header-title"><el-icon><Warning /></el-icon> 告警记录</span>
            <el-tag type="danger" effect="dark" class="alert-badge">
              {{ unhandledCount }} 未处理
            </el-tag>
          </div>
          <div class="header-right">
            <el-select v-model="filterForm.type" placeholder="告警类型" clearable style="width: 150px;">
              <el-option label="湿度过低" value="湿度过低" />
              <el-option label="设备离线" value="设备离线" />
              <el-option label="数据未更新" value="数据未更新" />
            </el-select>
            <el-select v-model="filterForm.status" placeholder="处理状态" clearable style="width: 150px;">
              <el-option label="未处理" value="未处理">
                <el-tag type="danger" size="small">未处理</el-tag>
              </el-option>
              <el-option label="处理中" value="处理中">
                <el-tag type="warning" size="small">处理中</el-tag>
              </el-option>
              <el-option label="已处理" value="已处理">
                <el-tag type="success" size="small">已处理</el-tag>
              </el-option>
              <el-option label="已忽略" value="已忽略">
                <el-tag type="info" size="small">已忽略</el-tag>
              </el-option>
            </el-select>
            <el-date-picker
              v-model="filterForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 260px;"
            />
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" plain @click="refreshAlerts">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table 
        :data="paginatedAlerts" 
        border 
        stripe
        v-loading="loading"
        highlight-current-row
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="alertId" label="告警ID" width="100" />
        <el-table-column prop="alertType" label="告警类型" width="120">
          <template #default="scope">
            <el-tag :type="ALERT_TYPE_CONFIG[scope.row.alertType]?.type || 'info'" size="small" effect="dark">
              {{ scope.row.alertType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="plotName" label="关联地块" width="120" />
        <el-table-column prop="deviceId" label="设备ID" width="120">
          <template #default="scope">
            <el-link type="primary" :underline="false">{{ scope.row.deviceId }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="告警原因" min-width="200" show-overflow-tooltip>
          <template #default="scope">
            <span style="color: #606266;">{{ scope.row.reason }}</span>
          </template>
        </el-table-column>
        <el-table-column label="触发值/阈值" width="140">
          <template #default="scope">
            <div class="value-cell">
              <span class="trigger-value">{{ scope.row.triggerValue }}</span>
              <span class="divider">/</span>
              <span class="threshold-value">{{ scope.row.threshold }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="occurTime" label="发生时间" width="160" sortable />
        <el-table-column prop="handledAt" label="处理时间" width="160">
          <template #default="scope">
            <span v-if="scope.row.handledAt" class="recover-time">{{ scope.row.handledAt }}</span>
            <span v-else class="no-recover">尚未处理</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="处理状态" width="100" fixed="right">
          <template #default="scope">
            <el-tag :type="ALERT_STATUS_CONFIG[scope.row.status]?.type || 'info'" size="small" effect="dark">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="270" fixed="right">
          <template #default="scope">
            <div class="action-row">
                <el-button v-if="scope.row.status === '未处理'" type="primary" plain size="small" @click="handleConfirm(scope.row)"><el-icon><Check /></el-icon>确认告警</el-button>
                <el-button v-if="scope.row.status !== '未处理'" type="info" plain size="small" disabled><el-icon><SuccessFilled /></el-icon>{{ scope.row.status }}</el-button>
              <el-button type="primary" link size="small" @click="showDetail(scope.row)">详情</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="filteredAlerts.length"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 告警详情弹窗 -->
    <el-dialog v-model="detailDialog.visible" title="告警详情" width="600px">
      <el-descriptions :column="2" border v-if="detailDialog.data">
        <el-descriptions-item label="告警ID" :span="2">{{ detailDialog.data.alertId }}</el-descriptions-item>
        <el-descriptions-item label="告警类型">
          <el-tag :type="ALERT_TYPE_CONFIG[detailDialog.data.alertType]?.type || 'info'">
            {{ detailDialog.data.alertType }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="处理状态">
          <el-tag :type="ALERT_STATUS_CONFIG[detailDialog.data.status]?.type || 'info'" effect="dark">
            {{ detailDialog.data.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="关联地块">{{ detailDialog.data.plotName }}</el-descriptions-item>
        <el-descriptions-item label="设备ID">{{ detailDialog.data.deviceId }}</el-descriptions-item>
        <el-descriptions-item label="触发值">{{ detailDialog.data.triggerValue }}</el-descriptions-item>
        <el-descriptions-item label="阈值">{{ detailDialog.data.threshold }}</el-descriptions-item>
        <el-descriptions-item label="发生时间">{{ detailDialog.data.occurTime }}</el-descriptions-item>
        <el-descriptions-item label="处理时间">
          {{ detailDialog.data.handledAt || '尚未处理' }}
        </el-descriptions-item>
        <el-descriptions-item label="告警原因" :span="2">{{ detailDialog.data.reason }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ALERT_TYPE_CONFIG, ALERT_STATUS_CONFIG } from '@/utils/farmAdminStatus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { normalizeAlert, parseDate } from '@/utils/dataAdapters'
import { usePlatformStore } from '@/stores/platform'
import { acknowledgeAlert } from '@/api/alert'

const loading = ref(false)
const alertList = ref([])
const userStore = useUserStore()

const filterForm = ref({
  type: '',
  status: '',
  dateRange: null
})

const pagination = ref({
  page: 1,
  pageSize: 10
})

const detailDialog = ref({
  visible: false,
  data: null
})

const platformStore = usePlatformStore()
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

async function loadAlerts(force = false) {
  loading.value = true
  try {
    await platformStore.loadData(force)
    const scoped = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
    const farmIds = scoped.length ? scoped : platformStore.farms.map((farm) => String(farm.farmId))
    const plotIds = platformStore.plots.filter((plot) => farmIds.includes(String(plot.farmId))).map((plot) => String(plot.plotNo))
    alertList.value = platformStore.alerts.filter((alert) => plotIds.includes(String(alert.plotId || alert.plotNo))).map((alert) => {
      const normalized = normalizeAlert(alert)
      return {
        ...alert,
        alertId: normalized.alertId,
        alertType: normalized.type,
        plotName: alert.plotName || normalized.plotId,
        reason: normalized.description,
        triggerValue: normalized.value,
        threshold: normalized.threshold,
        occurTime: normalized.occurTime,
        handledAt: normalized.handledAt || alert.recoverTime || '',
        status: normalized.status,
      }
    })
  } catch (error) {
    ElMessage.error(error.message || '告警数据加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => loadAlerts())

const filteredAlerts = computed(() => {
  let result = alertList.value
  if (filterForm.value.type) {
    result = result.filter(a => a.alertType === filterForm.value.type)
  }
  if (filterForm.value.status) {
    result = result.filter(a => a.status === filterForm.value.status)
  }
  if (filterForm.value.dateRange?.length === 2) {
    const [start, end] = filterForm.value.dateRange
    const endOfDay = new Date(end)
    endOfDay.setHours(23, 59, 59, 999)
    result = result.filter((alert) => {
      const time = parseDate(alert.occurTime)?.getTime()
      return time && time >= start.getTime() && time <= endOfDay.getTime()
    })
  }
  return result
})

const paginatedAlerts = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return filteredAlerts.value.slice(start, end)
})

const unhandledCount = computed(() => alertList.value.filter(a => a.status === '未处理').length)

const handleSearch = () => {
  pagination.value.page = 1
  ElMessage.success('查询完成')
}

const handleReset = () => {
  filterForm.value = { type: '', status: '', dateRange: null }
  pagination.value.page = 1
}

const refreshAlerts = async () => {
  await loadAlerts(true)
  ElMessage.success('告警列表已刷新')
}

const handleConfirm = (alert) => {
  ElMessageBox.confirm(
    `确认已知晓告警 ${alert.alertId}？`,
    '确认告警',
    { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    if (!isMock) await acknowledgeAlert(alert.alertId)
    const idx = alertList.value.findIndex(a => a.alertId === alert.alertId)
    if (idx !== -1) alertList.value[idx].status = '处理中'
    ElMessage.success('告警已确认')
  })
}

const showDetail = (alert) => {
  detailDialog.value = { visible: true, data: { ...alert } }
}

const handleSizeChange = (size) => { pagination.value.pageSize = size }
const handlePageChange = (page) => { pagination.value.page = page }
</script>

<style scoped>
.alerts-page { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.page-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; }
.alert-summary { min-width: 108px; display: flex; align-items: baseline; justify-content: center; gap: 5px; padding: 10px 14px; border: 1px solid #f0dddd; border-radius: 12px; color: #a84d4d; background: #fff7f7; }
.alert-summary strong { font-size: 22px; }.alert-summary span { font-size: 12px; }
.alerts-card { border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 8px 28px rgba(20, 69, 53, .05); overflow: hidden; }
.alerts-card :deep(.el-card__header) { padding: 18px 20px; border-bottom-color: #edf2ef; }
.alerts-card :deep(.el-card__body) { padding: 0 20px 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; gap: 18px; }
.header-left { display: flex; align-items: center; gap: 11px; white-space: nowrap; }
.header-title { display: flex; align-items: center; gap: 8px; color: #28483d; font-size: 16px; font-weight: 700; }
.header-title .el-icon { color: var(--accent); }
.alert-badge { border: 0; border-radius: 8px; font-size: 12px; }
.header-right { display: flex; flex: 1; justify-content: flex-end; align-items: center; flex-wrap: wrap; gap: 9px; }
.header-right :deep(.el-input__wrapper), .header-right :deep(.el-select__wrapper) { border-radius: 9px; box-shadow: 0 0 0 1px #dce8e3 inset; }
.header-right :deep(.el-button) { margin-left: 0; border-radius: 9px; }
.header-right :deep(.el-button--primary) { border-color: var(--accent); background: var(--accent); }
.alerts-card :deep(.el-table) { --el-table-header-bg-color: #f3f8f5; --el-table-header-text-color: #526a61; --el-table-row-hover-bg-color: #f5faf7; margin-top: 20px; border-radius: 10px; }
.alerts-card :deep(.el-table th.el-table__cell) { height: 46px; font-weight: 650; }
.alerts-card :deep(.el-table td.el-table__cell) { padding: 10px 0; }
.value-cell { display: flex; align-items: center; gap: 5px; }
.trigger-value { color: #d95858; font-weight: 700; }
.divider { color: #bdc7c3; }
.threshold-value { color: #82918c; }
.recover-time { color: #2d9466; }
.no-recover { color: #aeb9b5; }
.action-row { display: flex; align-items: center; flex-wrap: nowrap; gap: 8px; white-space: nowrap; }
.action-row :deep(.el-button) { margin: 0; padding: 6px 9px; border-radius: 7px; }
.action-row :deep(.el-button.is-link) { padding-right: 2px; padding-left: 2px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 20px; }
@media (max-width: 1280px) { .card-header { align-items: flex-start; flex-direction: column; }.header-right { justify-content: flex-start; width: 100%; } }
@media (max-width: 720px) { .page-head { flex-direction: column; }.alert-summary { margin-top: -10px; }.alerts-card :deep(.el-card__body) { padding: 0 12px 14px; }.header-right { align-items: stretch; flex-direction: column; }.header-right :deep(.el-select), .header-right :deep(.el-date-editor) { width: 100% !important; }.pagination-wrapper { justify-content: flex-start; overflow-x: auto; } }
</style>
