<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useFarmerStore } from '@/stores/farmer'
import Monitor from './Monitor.vue'
import History from './History.vue'
import PlantingInfo from './PlantingInfo.vue'
import PlotTimeline from '@/components/PlotTimeline.vue'

const route = useRoute()
const store = useFarmerStore()

watch(
  () => route.query.plotId,
  (plotId) => {
    if (typeof plotId === 'string') store.selectPlot(plotId)
  },
  { immediate: true },
)
</script>

<template>
  <div class="farmer-page management-page">
    <div class="page-head management-head">
      <div>
        <h1 class="page-title">地块管理</h1>
        <p class="page-subtitle">集中查看当前地块的实时状态、设备信息和历史数据。</p>
      </div>
      <div class="page-actions">
        <div class="filter-control plot-filter">
          <span class="filter-label"><el-icon><Location /></el-icon> 当前地块</span>
          <el-select class="plot-select" size="large" :model-value="store.selectedPlotId" @change="store.selectPlot">
            <el-option v-for="item in store.accessiblePlots" :key="item.plotId" :label="`${item.farmName} · ${item.plotName}`" :value="item.plotId" />
          </el-select>
        </div>
      </div>
    </div>

    <PlotTimeline />
    <PlantingInfo />
    <Monitor />
    <History />
  </div>
</template>

<style scoped>
.management-head{margin-bottom:20px}.management-page>:deep(.farmer-page){padding:0}
</style>
