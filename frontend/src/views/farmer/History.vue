<script setup>
import { computed, ref, watch } from 'vue'
import { useFarmerStore } from '@/stores/farmer'
import TrendChart from '@/components/TrendChart.vue'
import { parseDate } from '@/utils/dataAdapters'

const store = useFarmerStore()
const period = ref('24h')
const dateRange = ref([])
const plot = computed(() => store.currentPlot)
const trend = computed(() => store.getTrend(plot.value?.plotId, period.value))
const records = computed(() => store.visibleRecords.filter((item) => {
  if (item.plotId !== plot.value?.plotId) return false
  if (period.value !== 'custom' || dateRange.value?.length !== 2) return true
  const time = parseDate(item.startTime)?.getTime()
  return time && time >= dateRange.value[0].getTime() && time <= dateRange.value[1].getTime()
}))

watch([() => plot.value?.plotId, period, dateRange], ([plotId, currentPeriod, range]) => {
  if (!plotId || (currentPeriod === 'custom' && range?.length !== 2)) return
  store.loadHistory(plotId, currentPeriod, range).catch(() => {})
}, { immediate: true, deep: true })

const effect = computed(() => {
  const values = trend.value.soilHumidity
  const before = values.length ? Math.min(...values) : null
  const after = values.length ? values[values.length - 1] : null
  return {
    before,
    after,
    increase: before === null || after === null ? null : Math.max(0, +(after - before).toFixed(1)),
    count: records.value.filter((item) => item.operationType === '开启').length,
    targetTime: after === null ? '暂无数据' : after >= plot.value?.threshold ? '已达到' : '尚未达到',
  }
})

const devices = computed(() => {
  if (!plot.value) return []
  if (plot.value.deviceList?.length) return plot.value.deviceList.map((device) => ({
    ...device,
      status: device.online ? (device.type.includes('灌溉') && plot.value.irrigating ? '运行中' : '在线') : '离线',
    last: device.lastHeartbeat || '-',
    data: device.type.includes('温度') ? `${plot.value.temperature}℃` : device.type.includes('湿度') ? `${plot.value.humidity}%` : plot.value.irrigating ? '灌溉中' : '已关闭',
  }))
  return Object.values(plot.value.devices || {}).filter(Boolean).map((device) => ({
    ...device, status: plot.value.deviceOnline ? (device.type?.includes('灌溉') && plot.value.irrigating ? '运行中' : '在线') : '离线', last: plot.value.lastHeartbeat || '-',
    data: device.type?.includes('温度') ? `${plot.value.temperature}℃` : device.type?.includes('湿度') ? `${plot.value.humidity}%` : plot.value.irrigating ? '灌溉中' : '已关闭',
  }))
})
</script>

<template>
  <div class="farmer-page">
    <section class="content-panel chart-panel">
      <div class="section-head chart-head">
        <div class="chart-title"><h3>{{ plot?.plotName }} 温湿度变化</h3><p>图中同时展示湿度阈值线和灌溉事件标记</p></div>
        <div class="range-fields">
          <el-radio-group v-model="period">
            <el-radio-button value="24h">近24小时</el-radio-button>
            <el-radio-button value="7d">近7天</el-radio-button>
            <el-radio-button value="custom">自定义</el-radio-button>
          </el-radio-group>
          <el-date-picker v-if="period === 'custom'" v-model="dateRange" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" />
        </div>
        <div class="legend-notes"><span><i class="threshold"></i>湿度阈值 {{ plot?.threshold }}%</span><span><i class="irrigation"></i>灌溉事件</span></div>
      </div>
      <TrendChart v-if="trend.times?.length" :data="trend" :height="380" />
      <el-empty v-else description="所选时间范围内暂无监测数据" />
    </section>

    <section class="farmer-stat-grid effect-grid">
      <div class="farmer-stat"><div class="stat-symbol blue"><el-icon><Bottom /></el-icon></div><div><label>范围内最低湿度</label><strong>{{ effect.before ?? '-' }}{{ effect.before === null ? '' : '%' }}</strong><small>所选时间范围</small></div></div>
      <div class="farmer-stat"><div class="stat-symbol"><el-icon><Top /></el-icon></div><div><label>最新湿度</label><strong>{{ effect.after ?? '-' }}{{ effect.after === null ? '' : '%' }}</strong><small>{{ effect.increase === null ? '暂无对比数据' : `提升 ${effect.increase} 个百分点` }}</small></div></div>
      <div class="farmer-stat"><div class="stat-symbol orange"><el-icon><Timer /></el-icon></div><div><label>达到目标耗时</label><strong>{{ effect.targetTime }}</strong><small>目标 {{ plot?.threshold }}%</small></div></div>
      <div class="farmer-stat"><div class="stat-symbol"><el-icon><Refresh /></el-icon></div><div><label>近期灌溉次数</label><strong>{{ effect.count }}</strong><small>记录可追溯</small></div></div>
    </section>

    <section class="content-panel">
      <div class="section-head"><div><h3>灌溉事件记录</h3><p>用于对照灌溉前后的湿度变化</p></div></div>
      <el-table :data="records" class="compact-table">
        <el-table-column prop="startTime" label="开始时间" min-width="170" />
        <el-table-column prop="endTime" label="结束时间" min-width="170"><template #default="scope">{{ scope.row.endTime || '进行中' }}</template></el-table-column>
        <el-table-column prop="duration" label="时长（分钟）" width="120" />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column prop="operationType" label="动作" width="90" />
        <el-table-column prop="activationType" label="触发方式" width="110" />
        <el-table-column prop="status" label="结果" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === '失败' ? 'danger' : scope.row.status === '进行中' ? 'info' : '']">{{ scope.row.status }}</span></template></el-table-column>
      </el-table>
    </section>

    <section class="content-panel device-panel">
      <div class="section-head"><div><h3>设备运行状态</h3><p>查看当前地块各类设备的在线状态、实时数据和最后心跳</p></div></div>
      <el-table :data="devices" class="compact-table">
        <el-table-column prop="id" label="设备ID" width="85" />
        <el-table-column prop="deviceNo" label="设备编号" min-width="125" />
        <el-table-column prop="type" label="设备类型" min-width="120" />
        <el-table-column label="状态" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === '离线' ? 'danger' : scope.row.status === '运行中' ? 'info' : '']">{{ scope.row.status }}</span></template></el-table-column>
        <el-table-column prop="data" label="当前数据" min-width="100" />
        <el-table-column prop="last" label="最后心跳" min-width="170" />
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.chart-head{display:grid;grid-template-columns:minmax(220px,1fr) auto minmax(220px,1fr);align-items:start}.chart-title{justify-self:start}.range-fields{display:flex;align-items:center;justify-self:center;gap:10px}.range-fields :deep(.el-radio-button__inner){min-height:38px;display:flex;align-items:center;font-weight:600}.range-fields :deep(.el-radio-button__original-radio:checked+.el-radio-button__inner){background:#277e5b;border-color:#277e5b;box-shadow:-1px 0 0 0 #277e5b}.chart-panel{margin:18px 0}.device-panel{margin-top:18px}.legend-notes{display:flex;justify-self:end;gap:14px;padding-top:8px;color:#7d8d87;font-size:11px}.legend-notes span{display:flex;align-items:center;gap:5px}.legend-notes i{width:18px;height:2px;display:inline-block}.legend-notes .threshold{border-top:2px dashed #e49b4d}.legend-notes .irrigation{background:#2879a8}.effect-grid{margin-top:0}@media(max-width:1100px){.chart-head{grid-template-columns:1fr auto}.chart-title{grid-column:1}.range-fields{grid-column:2;justify-self:end}.legend-notes{grid-column:1/-1;grid-row:2;justify-self:end}}@media(max-width:900px){.chart-head{display:flex;align-items:flex-start;flex-direction:column}.range-fields{width:100%;align-items:stretch;flex-direction:column}.legend-notes{display:none}}
</style>
