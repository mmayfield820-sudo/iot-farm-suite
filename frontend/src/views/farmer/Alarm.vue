<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'
import { formatDateTime, parseDate } from '@/utils/dataAdapters'
import { disposePlanAdjustmentReminder, getPlanAdjustmentReminders } from '@/api/alert'

const store = useFarmerStore()
const userStore = useUserStore()
const filters = reactive({ plotId: '', type: '', status: '' })
const dateRange = ref([])
const detail = ref(null)
const reminders = ref([])
const disposition = reactive({ visible: false, item: null, action: '', note: '', submitting: false })
const reminderTypeLabel = { low_moisture: '土壤湿度偏低', continuous_rain: '连续降雨', device_offline: '设备离线' }
const dispositionLabel = { adjust_as_suggested: '按建议调整', keep_original_plan: '保持原计划', handled: '已处理' }

const alertTime = (value) => parseDate(value)?.getTime() || 0
const formatTimestamp = (value) => formatDateTime(value, '-')
const inDateRange = (item) => dateRange.value?.length !== 2 || (
  alertTime(item.occurTime) >= dateRange.value[0].getTime()
  && alertTime(item.occurTime) <= dateRange.value[1].getTime()
)
const filtered = computed(() => store.visibleAlerts.filter((item) => (
  (!filters.plotId || item.plotId === filters.plotId)
  && (!filters.type || item.type === filters.type)
  && (!filters.status || item.status === filters.status)
  && inDateRange(item)
)))

async function loadReminders() {
  try {
    reminders.value = await getPlanAdjustmentReminders()
  } catch (error) {
    ElMessage.error(error.message || '计划调整提醒加载失败')
  }
}

function openDisposition(item, action) {
  Object.assign(disposition, { visible: true, item, action, note: '' })
}

async function submitDisposition() {
  const note = disposition.note.trim()
  if (!note) return ElMessage.warning('请填写处理备注')
  disposition.submitting = true
  try {
    await disposePlanAdjustmentReminder(disposition.item.id, { action: disposition.action, note })
    reminders.value = reminders.value.filter((item) => item.id !== disposition.item.id)
    disposition.visible = false
    ElMessage.success('提醒处置已记录')
  } catch (error) {
    ElMessage.error(error.message || '提醒处置失败')
  } finally {
    disposition.submitting = false
  }
}

function confirmAlert(item) {
  ElMessageBox.confirm(`确认已知晓 ${item.plotName} 的“${item.type}”告警？`, '确认告警', { type: 'warning' })
    .then(async () => {
      try {
        await store.acknowledge(item.alertId)
        ElMessage.success('告警已确认')
      } catch (error) {
        ElMessage.error(error.message || '更新失败')
      }
    })
}

function resetFilters() {
  Object.assign(filters, { plotId: '', type: '', status: '' })
  dateRange.value = []
}

onMounted(loadReminders)
</script>

<template>
  <div class="farmer-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">告警中心</h1>
        <p class="page-subtitle">查看告警原因、关联地块、实时数据和完整处理状态。</p>
      </div>
      <div class="page-actions"><span class="status-pill danger">{{ store.unhandledCount }} 项待处理</span></div>
    </div>

    <section v-if="reminders.length" class="content-panel reminder-panel">
      <div class="section-head">
        <div><h3>计划调整提醒</h3><p>以下情况可能影响既有灌溉或巡园安排。</p></div>
        <span class="status-pill warning">{{ reminders.length }} 项待关注</span>
      </div>
      <div class="reminder-list">
        <article v-for="item in reminders" :key="item.id" class="reminder-item">
          <div class="reminder-main">
            <div class="reminder-title"><strong>{{ item.plotName }}</strong><span class="status-pill warning">{{ reminderTypeLabel[item.type] || item.type }}</span></div>
            <p>{{ item.description }}</p>
            <div v-if="item.affectedTasks?.length" class="task-tags"><span v-for="task in item.affectedTasks" :key="task.id">{{ task.title }} · {{ task.scheduledDate }}</span></div>
          </div>
          <div class="reminder-side">
            <div class="reminder-actions">
              <el-button size="small" type="primary" plain @click="openDisposition(item, 'adjust_as_suggested')">按建议调整</el-button>
              <el-button size="small" @click="openDisposition(item, 'keep_original_plan')">保持原计划</el-button>
              <el-button size="small" type="info" plain @click="openDisposition(item, 'handled')">已处理</el-button>
            </div>
            <time>{{ formatTimestamp(item.triggeredAt) }}</time>
          </div>
        </article>
      </div>
    </section>

    <section class="content-panel">
      <div class="filter-bar">
        <el-select v-model="filters.plotId" clearable placeholder="全部地块"><el-option v-for="item in store.accessiblePlots" :key="item.plotId" :label="item.plotName" :value="item.plotId" /></el-select>
        <el-select v-model="filters.type" clearable placeholder="告警类型"><el-option v-for="item in ['超过阈值', '湿度过低', '湿度偏高', '长期没被访问', '设备故障', '设备离线', '灌溉失败']" :key="item" :label="item" :value="item" /></el-select>
        <el-select v-model="filters.status" clearable placeholder="处理状态"><el-option v-for="item in ['未处理', '处理中', '已处理', '已忽略']" :key="item" :label="item" :value="item" /></el-select>
        <el-date-picker v-model="dateRange" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" clearable />
        <el-button @click="resetFilters">重置</el-button>
      </div>
      <el-table :data="filtered" class="compact-table" stripe>
        <el-table-column label="发生时间" min-width="165"><template #default="scope">{{ formatTimestamp(scope.row.occurTime) }}</template></el-table-column>
        <el-table-column prop="plotName" label="地块" min-width="110" />
        <el-table-column prop="type" label="告警类型" min-width="130"><template #default="scope"><span :class="['status-pill', scope.row.level === '高' ? 'danger' : 'warning']">{{ scope.row.type }}</span></template></el-table-column>
        <el-table-column prop="reason" label="告警原因" min-width="260" show-overflow-tooltip />
        <el-table-column label="实时值 / 阈值" min-width="130"><template #default="scope"><b class="danger-value">{{ scope.row.value }}</b> / {{ scope.row.threshold }}</template></el-table-column>
        <el-table-column prop="status" label="状态" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === '未处理' ? 'danger' : scope.row.status === '处理中' ? 'warning' : '']">{{ scope.row.status }}</span></template></el-table-column>
        <el-table-column label="操作" width="190" fixed="right"><template #default="scope"><div class="action-row"><el-button v-if="scope.row.status === '未处理' && userStore.can('alert', 'modify')" size="small" type="primary" plain @click="confirmAlert(scope.row)"><el-icon><Check /></el-icon>确认告警</el-button><el-button v-if="['处理中', '已处理', '已忽略'].includes(scope.row.status)" size="small" type="info" plain disabled><el-icon><SuccessFilled /></el-icon>{{ scope.row.status }}</el-button><el-button size="small" link type="primary" @click="detail = scope.row">详情</el-button></div></template></el-table-column>
      </el-table>
      <el-empty v-if="!filtered.length" description="暂无符合条件的告警" />
    </section>

    <el-dialog v-model="disposition.visible" :title="dispositionLabel[disposition.action] || '提醒处置'" width="460px">
      <el-form label-position="top"><el-form-item label="处理备注"><el-input v-model="disposition.note" type="textarea" :rows="4" maxlength="1000" show-word-limit /></el-form-item></el-form>
      <template #footer><el-button @click="disposition.visible = false">取消</el-button><el-button type="primary" :loading="disposition.submitting" @click="submitDisposition">确认</el-button></template>
    </el-dialog>

    <el-dialog :model-value="Boolean(detail)" title="告警详情" width="600px" @close="detail = null">
      <el-descriptions v-if="detail" :column="2" border>
        <el-descriptions-item label="告警编号">{{ detail.alertId }}</el-descriptions-item><el-descriptions-item label="处理状态">{{ detail.status }}</el-descriptions-item><el-descriptions-item label="关联地块">{{ detail.plotName }}</el-descriptions-item><el-descriptions-item label="关联设备">{{ detail.deviceId }}</el-descriptions-item><el-descriptions-item label="触发值">{{ detail.value }}</el-descriptions-item><el-descriptions-item label="判断阈值">{{ detail.threshold }}</el-descriptions-item><el-descriptions-item label="发生时间" :span="2">{{ formatTimestamp(detail.occurTime) }}</el-descriptions-item><el-descriptions-item label="处理人">{{ detail.handledBy || '尚未处理' }}</el-descriptions-item><el-descriptions-item label="处理时间">{{ detail.handledAt ? formatTimestamp(detail.handledAt) : '尚未处理' }}</el-descriptions-item><el-descriptions-item label="告警原因" :span="2">{{ detail.reason }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<style scoped>
.reminder-panel { margin-bottom: 18px; border-color: #eadbb9; background: #fffdf7; }
.reminder-list { display: grid; gap: 10px; }
.reminder-item { display: flex; justify-content: space-between; gap: 16px; padding: 13px; border: 1px solid #eee3c9; border-radius: 8px; background: #fff; }
.reminder-main { min-width: 0; }
.reminder-title { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.reminder-title strong { color: #435d4e; font-size: 14px; }
.reminder-main p { margin: 7px 0; color: #65766f; font-size: 13px; line-height: 1.6; }
.task-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.task-tags span { padding: 3px 7px; border-radius: 5px; color: #7a6432; background: #faf2dc; font-size: 12px; }
.reminder-side { display: flex; flex: 0 0 auto; flex-direction: column; align-items: flex-end; gap: 10px; }
.reminder-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px; }
.reminder-actions :deep(.el-button) { margin: 0; border-radius: 6px; }
.reminder-item time { color: #98a49e; font-size: 12px; }
.filter-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
.filter-bar .el-select { width: 170px; }
.filter-bar :deep(.el-date-editor) { width: 360px; }
.danger-value { color: #c45353; }
.action-row { display: flex; align-items: center; flex-wrap: nowrap; gap: 8px; white-space: nowrap; }
.action-row :deep(.el-button) { margin: 0; padding: 6px 9px; border-radius: 7px; }
.action-row :deep(.el-button.is-link) { padding-right: 2px; padding-left: 2px; }
@media (max-width: 760px) { .reminder-item { flex-direction: column; gap: 10px; } .reminder-side { align-items: flex-start; } .reminder-actions { justify-content: flex-start; } .filter-bar :deep(.el-date-editor) { width: 100%; } }
</style>
