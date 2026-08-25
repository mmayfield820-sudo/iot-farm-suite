<script setup>
import { watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useFarmerStore } from '@/stores/farmer'
import Monitor from './Monitor.vue'
import History from './History.vue'

const route = useRoute()
const store = useFarmerStore()
const activeTab = computed(()=>{

return route.query.tab || 'monitor'

})

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

    <Monitor 
v-if="activeTab==='monitor'"
/>


<History 
v-if="activeTab==='history'"
/>
  </div>
</template>

<style scoped>
.management-head{margin-bottom:20px}.management-page>:deep(.farmer-page){padding:0}.filter-control{min-width:280px;padding:10px 12px;border:1px solid #b9d9ca;border-radius:14px;background:linear-gradient(135deg,#f5fbf8,#fff);box-shadow:0 7px 18px rgba(31,122,91,.1)}.filter-label{display:flex;align-items:center;gap:6px;margin-bottom:7px;color:#287b5d;font-size:12px;font-weight:700}.plot-select{width:100%}.plot-select:deep(.el-select__wrapper){min-height:42px;border-radius:10px;box-shadow:0 0 0 1px #9ecdb8 inset!important}.plot-select:deep(.el-select__selected-item){color:#244b3d;font-weight:700}@media(max-width:760px){.filter-control{width:100%;min-width:0}}
</style>
