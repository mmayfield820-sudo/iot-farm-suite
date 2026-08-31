<script setup>
import { computed, ref, watch } from 'vue'
import { useFarmerStore } from '@/stores/farmer'
import TrendChart from '@/components/TrendChart.vue'
import { formatDateTime, parseDate } from '@/utils/dataAdapters'
import { getPlotManagementHistory } from '@/api/history'

const store = useFarmerStore()
const period = ref('24h')
const dateRange = ref([])
const managementHistory = ref({ events: [] })
const historyLoading = ref(false)
const plot = computed(() => store.currentPlot)
const trend = computed(() => store.getTrend(plot.value?.plotId, period.value))
const isMock = import.meta.env.VITE_USE_MOCK === 'true'

const eventTypeLabel = { plan_task: '计划任务', task_completion: '完成记录', irrigation: '灌溉记录', alert: '告警' }
const eventTypeTone = { plan_task: 'primary', task_completion: 'success', irrigation: 'info', alert: 'danger' }
const eventStatusLabel = {
  pending: '待执行', in_progress: '执行中', completed: '已完成', overdue: '已逾期', cancelled: '已取消',
  success: '成功', failed: '失败', timeout: '超时', active: '未处理', acknowledged: '处理中', recovered: '已恢复',
}

function historyRange() {
  const to = period.value === 'custom' ? dateRange.value[1] : new Date()
  const from = period.value === 'custom'
    ? dateRange.value[0]
    : new Date(to.getTime() - (period.value === '7d' ? 7 * 24 : 24) * 60 * 60 * 1000)
  return { from, to }
}

function mockEvents(plotId, from, to) {
  const within = (value) => {
    const time = parseDate(value)?.getTime()
    return time && time >= from.getTime() && time <= to.getTime()
  }
  const irrigation = store.visibleRecords.filter((item) => item.plotId === plotId && within(item.startTime)).map((item) => ({
    id: `irrigation:${item.recordId}`, type: 'irrigation', occurredAt: item.startTime,
    title: `${item.operationType}灌溉`, description: `${item.activationType}触发；执行结果：${item.status}`,
    status: item.status, referenceId: item.recordId,
  }))
  const alerts = store.visibleAlerts.filter((item) => item.plotId === plotId && within(item.occurTime)).map((item) => ({
    id: `alert:${item.alertId}`, type: 'alert', occurredAt: item.occurTime, title: item.type,
    description: item.reason, status: item.status, referenceId: item.alertId,
  }))
  return [...irrigation, ...alerts].sort((left, right) => (parseDate(right.occurredAt) || 0) - (parseDate(left.occurredAt) || 0))
}

async function loadManagementHistory(plotId) {
  const { from, to } = historyRange()
  if (isMock) {
    managementHistory.value = { events: mockEvents(plotId, from, to) }
    return
  }
  historyLoading.value = true
  try {
    managementHistory.value = await getPlotManagementHistory(plotId, { from: from.toISOString(), to: to.toISOString() })
  } finally {
    historyLoading.value = false
  }
}

watch([() => plot.value?.plotId, period, dateRange], ([plotId, currentPeriod, range]) => {
  if (!plotId || (currentPeriod === 'custom' && range?.length !== 2)) return
  store.loadHistory(plotId, currentPeriod, range).catch(() => {})
  loadManagementHistory(plotId).catch(() => { managementHistory.value = { events: [] } })
}, { immediate: true, deep: true })

const eventTime = (value) => formatDateTime(value, '-')
const eventStatus = (value) => eventStatusLabel[value] || value || '-'
</script>

<template>
  <div class="farmer-page">
    <section class="content-panel chart-panel">
      <div class="section-head chart-head">
        <div class="chart-title"><h3>{{ plot?.plotName }} 温湿度变化</h3><p>图中同时展示湿度阈值线和灌溉事件标记</p></div>
        <div class="range-fields">
          <el-radio-group v-model="period"><el-radio-button value="24h">近24小时</el-radio-button><el-radio-button value="7d">近7天</el-radio-button><el-radio-button value="custom">自定义</el-radio-button></el-radio-group>
          <el-date-picker v-if="period === 'custom'" v-model="dateRange" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" />
        </div>
        <div class="legend-notes"><span><i class="threshold"></i>湿度阈值 {{ plot?.threshold }}%</span><span><i class="irrigation"></i>灌溉事件</span></div>
      </div>
      <TrendChart v-if="trend.times?.length" :data="trend" :height="380" />
      <el-empty v-else description="所选时间范围内暂无监测数据" />
    </section>

    <section class="content-panel timeline-panel" v-loading="historyLoading">
      <div class="section-head"><div><h3>地块管理记录</h3><p>计划任务、完成记录、灌溉记录和告警按时间汇总。</p></div></div>
      <el-timeline v-if="managementHistory.events?.length" class="management-timeline">
        <el-timeline-item v-for="item in managementHistory.events" :key="item.id" :timestamp="eventTime(item.occurredAt)" placement="top" :type="eventTypeTone[item.type] || 'primary'">
          <div class="timeline-entry"><div class="timeline-title"><strong>{{ item.title }}</strong><span :class="['status-pill', eventTypeTone[item.type] === 'danger' ? 'danger' : eventTypeTone[item.type] === 'info' ? 'info' : '']">{{ eventTypeLabel[item.type] || item.type }}</span></div><p>{{ item.description }}</p><small>{{ eventStatus(item.status) }} · {{ item.referenceId }}</small></div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="所选时间范围内暂无管理记录" />
    </section>

  </div>
</template>

<style scoped>
.chart-head{display:grid;grid-template-columns:minmax(220px,1fr) auto minmax(220px,1fr);align-items:start}.chart-title{justify-self:start}.range-fields{display:flex;align-items:center;justify-self:center;gap:10px}.range-fields :deep(.el-radio-button__inner){min-height:38px;display:flex;align-items:center;font-weight:600}.range-fields :deep(.el-radio-button__original-radio:checked+.el-radio-button__inner){background:#277e5b;border-color:#277e5b;box-shadow:-1px 0 0 0 #277e5b}.chart-panel{margin:18px 0}.timeline-panel,.device-panel{margin-top:18px}.legend-notes{display:flex;justify-self:end;gap:14px;padding-top:8px;color:#7d8d87;font-size:11px}.legend-notes span{display:flex;align-items:center;gap:5px}.legend-notes i{width:18px;height:2px;display:inline-block}.legend-notes .threshold{border-top:2px dashed #e49b4d}.legend-notes .irrigation{background:#2879a8}.effect-grid{margin-top:0}.management-timeline{margin:8px 0 0;padding-left:6px}.timeline-entry{padding:2px 0 10px}.timeline-title{display:flex;align-items:center;gap:8px}.timeline-title strong{color:#315347;font-size:14px}.timeline-entry p{margin:6px 0;color:#687a72;font-size:13px;line-height:1.55}.timeline-entry small{color:#98a69f;font-size:11px}@media(max-width:1100px){.chart-head{grid-template-columns:1fr auto}.chart-title{grid-column:1}.range-fields{grid-column:2;justify-self:end}.legend-notes{grid-column:1/-1;grid-row:2;justify-self:end}}@media(max-width:900px){.chart-head{display:flex;align-items:flex-start;flex-direction:column}.range-fields{width:100%;align-items:stretch;flex-direction:column}.legend-notes{display:none}}
</style>
