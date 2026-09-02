<script setup>
import { computed, ref, watch } from 'vue'
import { useFarmerStore } from '@/stores/farmer'
import TrendChart from '@/components/TrendChart.vue'

const props = defineProps({ productionContext: Object })
const store = useFarmerStore()
const period = ref('24h')
const dateRange = ref([])
const plot = computed(() => store.currentPlot)
const trend = computed(() => store.getTrend(plot.value?.plotId, period.value))
const targetMin = computed(() => props.productionContext?.stage?.moistureMin ?? plot.value?.threshold)
const targetMax = computed(() => props.productionContext?.stage?.moistureMax ?? null)

const devices = computed(() => {
  if (!plot.value) return []
  const source = plot.value.deviceList?.length
    ? plot.value.deviceList
    : Object.values(plot.value.devices || {}).filter(Boolean)

  return source.map((device) => {
    const type = device.type || '未知设备'
    const online = typeof device.online === 'boolean' ? device.online : plot.value.deviceOnline !== false
    const isIrrigationDevice = type.includes('灌溉')
    const running = typeof device.running === 'boolean'
      ? device.running
      : isIrrigationDevice ? plot.value.irrigating : online
    const data = type.includes('温度')
      ? `${plot.value.temperature}℃`
      : type.includes('湿度')
        ? `${plot.value.humidity}%`
        : isIrrigationDevice
          ? plot.value.irrigating ? '灌溉中' : '已关闭'
          : device.latestValue ?? '-'

    return {
      ...device,
      type,
      communicationStatus: online ? '在线' : '离线',
      collectionStatus: device.workStatus || (running ? '运行中' : '已停止采集'),
      data,
      last: device.lastHeartbeat || plot.value.lastHeartbeat || '-',
    }
  })
})

watch([() => plot.value?.plotId, period, dateRange], ([plotId, currentPeriod, range]) => {
  if (!plotId || (currentPeriod === 'custom' && range?.length !== 2)) return
  store.loadHistory(plotId, currentPeriod, range).catch(() => {})
}, { immediate: true, deep: true })
</script>

<template>
  <section class="history-trend-panel">
    <header class="history-head">
      <h2>历史数据趋势</h2>
      <el-radio-group v-model="period" class="period-switch">
        <el-radio-button value="24h">近24小时</el-radio-button>
        <el-radio-button value="7d">近7天</el-radio-button>
        <el-radio-button value="30d">近30天</el-radio-button>
        <el-radio-button value="custom"><el-icon><Calendar /></el-icon>自定义</el-radio-button>
      </el-radio-group>
    </header>
    <el-date-picker v-if="period === 'custom'" v-model="dateRange" class="custom-range" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" />
    <div v-if="trend.times?.length" class="chart-grid">
      <article class="metric-chart">
        <h3>土壤湿度（%）</h3>
        <TrendChart :data="trend" metric="moisture" :target-min="targetMin" :target-max="targetMax" :height="265" />
        <footer class="chart-notes"><span><i class="target"></i>目标区间（阶段建议）</span><span><i class="irrigation"></i>灌溉事件</span><span><i class="alert"></i>告警事件</span></footer>
      </article>
      <article class="metric-chart"><h3>环境温度（℃）</h3><TrendChart :data="trend" metric="temperature" :height="265" /></article>
    </div>
    <el-empty v-else description="所选时间范围内暂无监测数据" />
  </section>

  <section class="device-panel">
    <header class="device-head">
      <h2>设备状态</h2>
      <p>通信在线与是否正在采集分别显示，停止采集不等于设备离线</p>
    </header>
    <el-table :data="devices" class="compact-table" empty-text="当前地块暂无设备">
      <el-table-column prop="id" label="设备ID" width="90" />
      <el-table-column prop="deviceNo" label="设备编号" min-width="125" />
      <el-table-column prop="type" label="设备类型" min-width="120" />
      <el-table-column label="通信状态" width="105">
        <template #default="scope"><span :class="['status-pill', scope.row.communicationStatus === '离线' ? 'danger' : '']">{{ scope.row.communicationStatus }}</span></template>
      </el-table-column>
      <el-table-column label="采集状态" width="125">
        <template #default="scope"><span :class="['status-pill', scope.row.collectionStatus === '已停止采集' ? 'info' : '']">{{ scope.row.collectionStatus }}</span></template>
      </el-table-column>
      <el-table-column prop="data" label="当前数据" min-width="100" />
      <el-table-column prop="last" label="最后心跳" min-width="170" />
    </el-table>
  </section>
</template>

<style scoped>
.history-trend-panel,.device-panel{margin-top:18px;padding:20px 22px;border:1px solid #e8ece8;border-radius:9px;background:#fff;box-shadow:0 6px 18px rgba(27,67,46,.04)}.history-head{display:flex;align-items:center;justify-content:space-between;gap:18px}.history-head h2,.device-head h2{margin:0;color:#18271f;font-size:20px}.period-switch :deep(.el-radio-button__inner){min-width:96px;height:40px;display:flex;align-items:center;justify-content:center;gap:6px;padding:0 18px;color:#34423b;font-weight:600}.period-switch :deep(.el-radio-button__original-radio:checked+.el-radio-button__inner){border-color:#278047;background:#278047;box-shadow:-1px 0 0 #278047}.custom-range{display:flex;margin:14px 0 0 auto}.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:14px}.metric-chart{min-width:0;padding:17px 12px 10px;border:1px solid #e7ebe8;border-radius:8px}.metric-chart h3{margin:0 6px;color:#1e2d25;font-size:15px}.chart-notes{display:flex;align-items:center;gap:10px;margin:0 6px;padding-top:8px;border-top:1px solid #edf0ed;color:#68756e;font-size:11px}.chart-notes span{display:flex;align-items:center;gap:7px;padding:7px 11px;border-radius:6px;background:#f5f5f1;white-space:nowrap}.chart-notes i{display:inline-block;flex:0 0 auto}.chart-notes .target{width:18px;border-top:2px dashed #58a26b}.chart-notes .irrigation{width:11px;height:14px;border-radius:8px 8px 8px 2px;background:#1697e8;transform:rotate(45deg)}.chart-notes .alert{width:10px;height:10px;border-radius:50%;background:#f04c3a}.device-head{margin-bottom:14px}.device-head p{margin:6px 0 0;color:#68756e;font-size:13px}.device-panel :deep(.el-table__header-wrapper th){color:#20523d;background:#f5f8f3!important}.device-panel :deep(.el-table__row:hover>td.el-table__cell){background:#f7faf4}@media(max-width:1100px){.history-head{align-items:flex-start;flex-direction:column}.chart-grid{grid-template-columns:1fr}}@media(max-width:650px){.period-switch{display:grid;grid-template-columns:1fr 1fr;width:100%}.period-switch :deep(.el-radio-button__inner){width:100%;min-width:0}.chart-notes{align-items:flex-start;flex-direction:column}.device-panel{overflow-x:auto}.device-panel .compact-table{min-width:820px}}
.history-trend-panel{padding:16px 18px 12px}.history-head{align-items:center;flex-direction:row}.period-switch :deep(.el-radio-button__inner){height:38px}.chart-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:12px}.metric-chart{padding:14px 10px 8px}@media(max-width:650px){.history-head{align-items:flex-start;flex-direction:column}.history-trend-panel{overflow-x:auto}.chart-grid{grid-template-columns:repeat(2,minmax(380px,1fr));min-width:780px}}
</style>
