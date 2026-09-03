<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'
import { formatDateTime, parseDate } from '@/utils/dataAdapters'
import { getPlanAdjustmentReminders } from '@/api/alert'

const store = useFarmerStore()
const userStore = useUserStore()
const filters = reactive({ plotId: '', type: '', status: '' })
const dateRange = ref([])
const detail = ref(null)
const reminders = ref([])
const reminderTypeLabel = {
  continuous_rain: '连续降雨',
  high_rain_probability: '高降雨概率',
  high_temperature: '高温天气',
  frost_risk: '低温霜冻',
  strong_wind: '大风天气',
}

const alertTime = (value) => parseDate(value)?.getTime() || 0
const formatTimestamp = (value) => formatDateTime(value, '-')
const inDateRange = (item) => dateRange.value?.length !== 2 || (
  alertTime(item.occurTime) >= dateRange.value[0].getTime()
  && alertTime(item.occurTime) <= dateRange.value[1].getTime()
)
const filtered = computed(() => store.farmAlerts.filter((item) => (
  (!filters.plotId || item.plotId === filters.plotId)
  && (!filters.type || item.type === filters.type)
  && (!filters.status || item.status === filters.status)
  && inDateRange(item)
)))
const farmPlotIds = computed(() => new Set(store.farmPlots.map((plot) => plot.plotId)))
const farmReminders = computed(() => reminders.value.filter((item) => farmPlotIds.value.has(item.plotId)))

async function loadReminders() {
  try {
    reminders.value = await getPlanAdjustmentReminders()
  } catch (error) {
    ElMessage.error(error.message || '今日农事提醒加载失败')
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
        <p class="page-subtitle">查看普通告警和计划变更结果；新计划生成后无需农户再次操作。</p>
      </div>
    </div>

    <section class="alarm-overview">
      <div class="alarm-overview-item danger"><span><el-icon><Warning /></el-icon></span><div><small>待处理告警</small><strong>{{ store.unhandledCount }} <em>项</em></strong><p>需要尽快处理</p></div></div>
      <div class="alarm-overview-item warning"><span><el-icon><Warning /></el-icon></span><div><small>处理中告警</small><strong>{{ store.farmAlerts.filter((item) => item.status === '处理中').length }} <em>项</em></strong><p>正在处理中</p></div></div>
      <div class="alarm-overview-item success"><span><el-icon><CircleCheck /></el-icon></span><div><small>已处理告警</small><strong>{{ store.farmAlerts.filter((item) => ['已处理', '已忽略'].includes(item.status)).length }} <em>项</em></strong><p>无需处理</p></div></div>
    </section>

    <section class="content-panel reminder-panel">
      <div class="section-head">
        <div><h3>今日农事提醒</h3><p>天气情况可能影响今天的农事安排，请结合现场情况合理安排。</p></div>
        <span v-if="farmReminders.length" class="status-pill warning">{{ farmReminders.length }} 条</span>
      </div>
      <div v-if="farmReminders.length" class="reminder-list">
          <article v-for="item in farmReminders" :key="item.id" class="reminder-item">
          <div class="reminder-main">
            <div class="reminder-title"><strong>{{ item.plotName }}</strong><span class="status-pill warning">{{ reminderTypeLabel[item.type] || item.type }}</span></div>
            <p>{{ item.description }}</p>
            <div v-if="item.affectedTasks?.length" class="task-tags"><span v-for="task in item.affectedTasks" :key="task.id">{{ task.title }} · {{ task.scheduledDate }}</span></div>
          </div>
          <time>{{ formatTimestamp(item.triggeredAt) }}</time>
        </article>
      </div>
      <el-empty v-else :image-size="58" description="今天暂无天气影响提醒" />
    </section>

    <section class="content-panel">
      <div class="section-head"><div><h3>历史告警</h3></div></div>
      <div class="filter-bar">
        <el-select v-model="filters.plotId" clearable placeholder="全部地块"><el-option v-for="item in store.farmPlots" :key="item.plotId" :label="item.plotName" :value="item.plotId" /></el-select>
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

    <el-dialog :model-value="Boolean(detail)" title="告警详情" width="600px" @close="detail = null">
      <el-descriptions v-if="detail" :column="2" border>
        <el-descriptions-item label="告警编号">{{ detail.alertId }}</el-descriptions-item><el-descriptions-item label="处理状态">{{ detail.status }}</el-descriptions-item><el-descriptions-item label="关联地块">{{ detail.plotName }}</el-descriptions-item><el-descriptions-item label="关联设备">{{ detail.deviceId }}</el-descriptions-item><el-descriptions-item label="触发值">{{ detail.value }}</el-descriptions-item><el-descriptions-item label="判断阈值">{{ detail.threshold }}</el-descriptions-item><el-descriptions-item label="发生时间" :span="2">{{ formatTimestamp(detail.occurTime) }}</el-descriptions-item><el-descriptions-item label="处理人">{{ detail.handledBy || '尚未处理' }}</el-descriptions-item><el-descriptions-item label="处理时间">{{ detail.handledAt ? formatTimestamp(detail.handledAt) : '尚未处理' }}</el-descriptions-item><el-descriptions-item label="告警原因" :span="2">{{ detail.reason }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<style scoped>
.alarm-overview{display:grid;grid-template-columns:repeat(3,1fr);margin:0 0 14px;padding:24px 28px;border:1px solid #e7ebe6;border-radius:10px;background:#fff;box-shadow:0 7px 20px rgba(24,65,45,.045)}.alarm-overview-item{display:flex;align-items:center;gap:18px;padding:0 32px;border-right:1px solid #e5eae5}.alarm-overview-item:first-child{padding-left:0}.alarm-overview-item:last-child{border:0}.alarm-overview-item>span{display:grid;width:60px;height:60px;place-items:center;border-radius:50%;font-size:32px}.alarm-overview-item.danger>span{color:#e33d2e;background:#fdebe8}.alarm-overview-item.warning>span{color:#ed9c00;background:#fff4de}.alarm-overview-item.success>span{color:#167a42;background:#eff7ed}.alarm-overview-item small,.alarm-overview-item strong,.alarm-overview-item p{display:block}.alarm-overview-item small{color:#44524b;font-size:15px}.alarm-overview-item strong{margin:6px 0;color:#d83c31;font-size:30px;line-height:1}.alarm-overview-item.warning strong{color:#e99500}.alarm-overview-item.success strong{color:#17733d}.alarm-overview-item em{font-size:16px;font-style:normal}.alarm-overview-item p{margin:8px 0 0;color:#78837e;font-size:13px}
.reminder-panel { margin-bottom: 18px; border-color: #e7ebe6; background: #fff; }
.reminder-list { display: grid; gap: 10px; }
.reminder-item { display: flex; justify-content: space-between; gap: 16px; padding: 13px; border: 1px solid #eee3c9; border-radius: 8px; background: #fff; }
.reminder-main { min-width: 0; }
.reminder-title { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.reminder-title strong { color: #435d4e; font-size: 14px; }
.reminder-main p { margin: 7px 0; color: #65766f; font-size: 13px; line-height: 1.6; }
.task-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.task-tags span { padding: 3px 7px; border-radius: 5px; color: #7a6432; background: #faf2dc; font-size: 12px; }
.reminder-item time { color: #98a49e; font-size: 12px; }
  .filter-bar { display: flex; align-items: flex-end; flex-wrap: wrap; gap: 10px; width: 100%; margin-bottom: 18px; }
  .filter-bar .el-select { width: 170px; }
  .filter-bar :deep(.el-date-editor) { width: 360px; }
  .filter-bar :deep(.el-select__wrapper), .filter-bar :deep(.el-date-editor.el-input__wrapper) { height: 40px; min-height: 40px; box-sizing: border-box; }
  .filter-bar > .el-button { width: auto; min-width: 86px; height: 40px; margin: 0; }
  .danger-value { color: #c45353; }
@media(max-width:800px){.alarm-overview{grid-template-columns:1fr;padding:8px 20px}.alarm-overview-item,.alarm-overview-item:first-child{padding:16px 0;border-right:0;border-bottom:1px solid #e5eae5}.alarm-overview-item:last-child{border-bottom:0}}
.action-row { display: flex; align-items: center; flex-wrap: nowrap; gap: 8px; white-space: nowrap; }
.action-row :deep(.el-button) { margin: 0; padding: 6px 9px; border-radius: 7px; }
.action-row :deep(.el-button.is-link) { padding-right: 2px; padding-left: 2px; }
  @media (max-width: 760px) { .reminder-item { flex-direction: column; gap: 10px; } .filter-bar .el-select, .filter-bar :deep(.el-date-editor), .filter-bar > .el-button { width: 100%; } }
</style>
