<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePlatformStore } from '@/stores/platform'
import { parseDate } from '@/utils/dataAdapters'

const store = usePlatformStore()
const filters = reactive({ farmId: '', plotNo: '', type: '', status: '', range: [] })
const detail = ref(null)
const typeOptions = ['湿度过低', '设备离线', '设备故障', '灌溉失败']
const statusOptions = ['未处理', '处理中', '已处理']

const availablePlots = computed(() => store.plots.filter((plot) => !filters.farmId || plot.farmId === filters.farmId))
const rows = computed(() => store.alerts.filter((alert) => {
  if (filters.farmId && alert.farmId !== filters.farmId) return false
  if (filters.plotNo && alert.plotNo !== filters.plotNo) return false
  if (filters.type && alert.type !== filters.type) return false
  if (filters.status && alert.status !== filters.status) return false
  if (filters.range?.length === 2) {
    const occurredAt = parseDate(alert.occurTime)?.getTime() || 0
    return occurredAt >= filters.range[0].getTime() && occurredAt <= filters.range[1].getTime()
  }
  return true
}))

function handle(row) {
  ElMessageBox.confirm(`确认已知晓告警 ${row.id}？`, '确认告警', { type: 'warning' }).then(async () => {
    await store.handleAlert(row.id)
    ElMessage.success('告警已确认')
  })
}
</script>

<template>
  <div class="farmer-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">全系统告警</h1>
        <p class="page-subtitle">按农场、地块、类型、状态和时间范围追溯异常。</p>
      </div>
      <div class="page-actions"><span class="status-pill danger">{{ store.unhandledAlerts }} 项未处理</span></div>
    </div>

    <section class="content-panel">
      <div class="filters">
        <el-select v-model="filters.farmId" clearable placeholder="全部农场" @change="filters.plotNo = ''">
          <el-option v-for="farm in store.farms" :key="farm.farmId" :label="farm.name" :value="farm.farmId" />
        </el-select>
        <el-select v-model="filters.plotNo" clearable placeholder="全部地块">
          <el-option v-for="plot in availablePlots" :key="plot.plotNo" :label="`${plot.plotNo} · ${plot.name}`" :value="plot.plotNo" />
        </el-select>
        <el-select v-model="filters.type" clearable placeholder="告警类型">
          <el-option v-for="type in typeOptions" :key="type" :label="type" :value="type" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="处理状态">
          <el-option v-for="status in statusOptions" :key="status" :label="status" :value="status" />
        </el-select>
        <el-date-picker v-model="filters.range" type="datetimerange" range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间" />
      </div>

      <el-table :data="rows" class="compact-table">
        <el-table-column prop="occurTime" label="发生时间" min-width="165" />
        <el-table-column prop="farmName" label="农场" min-width="130" />
        <el-table-column prop="plotName" label="地块" min-width="110" />
        <el-table-column prop="type" label="类型" min-width="120">
          <template #default="scope"><span class="status-pill danger">{{ scope.row.type }}</span></template>
        </el-table-column>
        <el-table-column prop="deviceId" label="设备 ID" width="95" />
        <el-table-column label="触发值 / 阈值" min-width="130">
          <template #default="scope">{{ scope.row.value }} / {{ scope.row.threshold }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="scope"><span :class="['status-pill', scope.row.status === '未处理' ? 'danger' : '']">{{ scope.row.status }}</span></template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="scope">
            <el-button link type="primary" @click="detail = scope.row">详情</el-button>
            <el-button v-if="scope.row.status === '未处理'" link type="success" @click="handle(scope.row)">确认告警</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog :model-value="Boolean(detail)" title="告警详情与处理过程" width="620px" @close="detail = null">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="告警 ID">{{ detail.id }}</el-descriptions-item>
          <el-descriptions-item label="处理状态">{{ detail.status }}</el-descriptions-item>
          <el-descriptions-item label="农场">{{ detail.farmName }}</el-descriptions-item>
          <el-descriptions-item label="地块">{{ detail.plotName }}</el-descriptions-item>
          <el-descriptions-item label="设备">{{ detail.deviceId }}</el-descriptions-item>
          <el-descriptions-item label="告警类型">{{ detail.type }}</el-descriptions-item>
          <el-descriptions-item label="发生时间">{{ detail.occurTime }}</el-descriptions-item>
          <el-descriptions-item label="处理时间">{{ detail.handledAt || '尚未处理' }}</el-descriptions-item>
          <el-descriptions-item label="告警原因" :span="2">{{ detail.reason }}</el-descriptions-item>
        </el-descriptions>
        <el-timeline class="process">
          <el-timeline-item v-for="item in detail.process" :key="item" type="primary">{{ item }}</el-timeline-item>
        </el-timeline>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.filters { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
.filters .el-select { width: 150px; }
.process { margin-top: 22px; }
</style>
