<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useFarmerStore } from '@/stores/farmer'
import { getPlotProductionContext } from '@/api/production'
import Monitor from './Monitor.vue'
import History from './History.vue'

const route = useRoute()
const store = useFarmerStore()
const currentPlot = computed(() => store.currentPlot)
const productionContexts = ref({})
const productionContext = computed(() => productionContexts.value[currentPlot.value?.farmId] || null)
let contextRequestToken = 0

watch(
  () => route.query.plotId,
  (plotId) => {
    if (typeof plotId === 'string') store.selectPlot(plotId)
  },
  { immediate: true },
)

watch(() => store.farmPlots.map((plot) => `${plot.farmId}:${plot.plotId}`).join('|'), async () => {
  const token = ++contextRequestToken
  const representatives = [...new Map(store.farmPlots.map((plot) => [plot.farmId, plot])).values()]
  const entries = await Promise.all(representatives.map(async (plot) => {
    try {
      return [plot.farmId, await getPlotProductionContext(plot.plotId)]
    } catch {
      return [plot.farmId, null]
    }
  }))
  if (token === contextRequestToken) productionContexts.value = Object.fromEntries(entries)
}, { immediate: true })

function plantingDateFor(plot) {
  return productionContexts.value[plot.farmId]?.plantingDate || '未定植'
}
</script>

<template>
  <div class="farmer-page management-page">
    <div class="page-head management-head">
      <div>
        <h1 class="page-title">地块管理</h1>
        <p class="page-subtitle">集中查看当前地块的实时状态、设备信息和历史数据。</p>
      </div>
    </div>

    <div class="management-layout">
      <aside class="plot-list-panel">
        <div class="plot-list-heading"><b>我的地块</b><span>共 {{ store.farmPlots.length }} 块</span></div>
        <button v-for="item in store.farmPlots" :key="item.plotId" :class="['plot-choice', { active: item.plotId === currentPlot?.plotId }]" @click="store.selectPlot(item.plotId)">
          <strong>{{ item.plotName }}</strong><small>{{ item.plotId }}</small><span><el-icon><Location /></el-icon>{{ item.farmName || '未命名农场' }}</span><span><el-icon><Calendar /></el-icon>定植日期：{{ plantingDateFor(item) }}</span>
        </button>
      </aside>
      <div class="management-detail"><Monitor :production-context="productionContext" /><History :production-context="productionContext" /></div>
    </div>
  </div>
</template>

<style scoped>
.management-head{margin-bottom:20px}.management-page>:deep(.farmer-page){padding:0}.management-layout{display:grid;grid-template-columns:280px minmax(0,1fr);gap:20px}.plot-list-panel{min-height:660px;padding:16px;border:1px solid #e7ebe6;border-radius:10px;background:#fff;box-shadow:0 7px 20px rgba(24,65,45,.045)}.plot-list-heading{display:flex;align-items:baseline;gap:8px;margin:5px 4px 14px;color:#1d2b24}.plot-list-heading b{font-size:18px}.plot-list-heading span{font-size:14px}.plot-choice{display:grid;gap:8px;width:100%;margin-bottom:13px;padding:18px 17px;border:1px solid #edf0eb;border-radius:9px;color:#315046;background:#fff;text-align:left;cursor:pointer}.plot-choice:hover{border-color:#90bd9d;background:#fbfefb}.plot-choice.active{border-color:#278047;background:#f8fcf7;box-shadow:inset 0 0 0 1px #278047}.plot-choice strong{color:#17382a;font-size:18px}.plot-choice small{color:#51635b;font-size:14px}.plot-choice span{display:flex;align-items:center;gap:8px;color:#52675d;font-size:13px}.plot-choice .el-icon{color:#367e4c}.management-detail{min-width:0}.management-detail :deep(.chart-panel){margin-top:18px}@media(max-width:980px){.management-layout{grid-template-columns:1fr}.plot-list-panel{display:grid;grid-template-columns:repeat(3,1fr);min-height:0;gap:12px}.plot-list-heading{grid-column:1/-1;margin-bottom:0}.plot-choice{margin:0}}@media(max-width:620px){.plot-list-panel{grid-template-columns:1fr}.plot-choice{padding:14px}.management-head{margin-bottom:14px}}
.management-layout{grid-template-columns:245px minmax(0,1fr);gap:16px}@media(max-width:980px){.management-layout{grid-template-columns:1fr}}
</style>
