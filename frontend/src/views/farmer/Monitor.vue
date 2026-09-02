<script setup>
import { computed } from 'vue'
import { useFarmerStore } from '@/stores/farmer'
import PlotOverviewIcon from '@/components/PlotOverviewIcon.vue'
import { parseDate } from '@/utils/dataAdapters'

const props = defineProps({ productionContext: Object })
const store = useFarmerStore()
const plot = computed(() => store.currentPlot)

const dataUpdatedAt = computed(() => {
  const date = parseDate(plot.value?.updateTime)
  if (!date) return '暂无更新时间'
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(date).reduce((result, part) => ({ ...result, [part.type]: part.value }), {})
  return `${Number(parts.month)}/${Number(parts.day)} ${parts.hour}:${parts.minute} 更新`
})

const stageFact = computed(() => {
  const stage = props.productionContext?.stage
  if (!stage) return { value: plot.value?.cropStage || '未配置' }
  return { value: stage.name, suffix: stage.code ? `（${stage.code}）` : '' }
})
const facts = computed(() => [
  { key: 'moisture', label: '土壤湿度', value: plot.value?.humidity != null ? `${plot.value.humidity}%` : '-', details: [dataUpdatedAt.value] },
  { key: 'temperature', label: '环境温度', value: plot.value?.temperature != null ? `${plot.value.temperature}℃` : '-', details: [dataUpdatedAt.value] },
  { key: 'irrigation-status', label: '灌溉状态', value: plot.value?.irrigating ? '灌溉中' : '未灌溉' },
  { key: 'stage', label: '当前阶段', ...stageFact.value },
  { key: 'age', label: '树龄', value: props.productionContext?.treeAgeYears ? `第 ${props.productionContext.treeAgeYears} 年` : '未配置' },
])
</script>

<template>
  <section v-if="plot" class="plot-overview-panel">
    <h2>当前地块：<strong>{{ plot.plotName }}</strong></h2>
    <div class="overview-box">
      <h3>地块概况</h3>
      <dl>
        <div v-for="fact in facts" :key="fact.key" :class="fact.key">
          <PlotOverviewIcon :type="fact.key" />
          <span><dt>{{ fact.label }}</dt><dd><span class="fact-value-line"><span>{{ fact.value }}</span><span v-if="fact.suffix" class="fact-suffix">{{ fact.suffix }}</span></span><small v-for="detail in fact.details || []" :key="detail">{{ detail }}</small></dd></span>
        </div>
      </dl>
    </div>
  </section>
</template>

<style scoped>
.plot-overview-panel{width:100%;padding:15px 20px 16px;border:1px solid #e8ece8;border-radius:9px;background:#fff;box-shadow:0 6px 18px rgba(27,67,46,.04)}.plot-overview-panel h2{margin:0 0 10px;color:#192a22;font-size:20px}.plot-overview-panel h2 strong{color:#24803f}.overview-box{width:100%;padding:9px 12px 10px;border:1px solid #e8ece8;border-radius:8px;background:#fff}.overview-box h3{margin:0 0 5px 9px;color:#18271f;font-size:14px}.overview-box dl{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));margin:0}.overview-box dl>div{display:grid;grid-template-columns:28px minmax(0,1fr);align-items:start;gap:7px;min-width:0;min-height:76px;padding:4px 16px;border-right:1px solid #e5e9e6}.overview-box dl>div:last-child{border-right:0}.overview-box svg{margin-top:1px;color:#399451;font-size:24px}.overview-box dt{color:#65716b;font-size:13px;white-space:nowrap}.overview-box dd{min-width:0;margin:5px 0 0;color:#28372f;font-size:14px;font-weight:600;line-height:1.35}.fact-value-line{display:flex;align-items:baseline;flex-wrap:wrap;column-gap:5px;row-gap:1px}.fact-value-line>span:first-child{min-width:0}.fact-suffix{flex:0 0 auto;white-space:nowrap}.overview-box dd small{display:block;margin-top:3px;color:#85918b;font-size:10px!important;font-weight:400;line-height:1.3;white-space:nowrap}@media(max-width:760px){.overview-box{overflow-x:auto}.overview-box dl{min-width:900px}.plot-overview-panel{padding:14px 16px}}
</style>
