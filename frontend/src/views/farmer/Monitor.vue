<script setup>
import { computed } from 'vue'
import { useFarmerStore } from '@/stores/farmer'
import { formatDateTime } from '@/utils/dataAdapters'

const store = useFarmerStore()
const plot = computed(() => store.currentPlot)
const formatTimestamp = (value) => formatDateTime(value, '暂无时间')
</script>
<template>
  <div class="farmer-page">
    <template v-if="plot">
      <el-alert v-if="plot.dataState !== 'realtime'" title="当前数据并非实时数据" description="该设备数据更新时间较早，请检查网络和设备连接。" type="warning" show-icon :closable="false" class="notice" />
      <section class="content-panel plot-info">
          <div class="section-head"><div><h3>当前地块状态</h3><p>{{ plot.plotId }}</p></div><span :class="['status-pill', plot.deviceOnline ? '' : 'danger']">{{ plot.deviceOnline ? '设备在线' : '设备离线' }}</span></div>
          <dl>
            <div><dt>土壤湿度</dt><dd :class="{low: plot.humidity < plot.threshold}">{{ plot.humidity }}% <small>参考阈值 {{ plot.threshold }}%</small></dd></div>
            <div><dt>环境温度</dt><dd>{{ plot.temperature ?? '-' }}℃</dd></div>
            <div><dt>灌溉状态</dt><dd>{{ plot.irrigating ? '灌溉中' : '未灌溉' }}</dd></div>
            <div><dt>数据更新</dt><dd>{{ plot.dataState === 'realtime' ? '实时' : '延迟' }} <small>{{ formatTimestamp(plot.updateTime) }}</small></dd></div>
            <div><dt>作物</dt><dd>{{ plot.cropName }} · {{ plot.cropStage }}</dd></div>
            <div><dt>位置</dt><dd>{{ plot.location }}</dd></div>
            <div><dt>监测设备</dt><dd>{{ plot.sensorId || '未绑定' }}</dd></div>
            <div><dt>最近灌溉</dt><dd>{{ plot.lastIrrigation ? formatTimestamp(plot.lastIrrigation) : '暂无记录' }}</dd></div>
          </dl>
      </section>
    </template>
  </div>
</template>
<style scoped>.notice{margin:4px 0 18px;border-radius:8px}.plot-info{margin-bottom:18px}.plot-info dl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1px;margin:0;border:1px solid #e8efeb;border-radius:8px;overflow:hidden}.plot-info dl div{display:flex;align-items:center;justify-content:space-between;gap:14px;min-height:48px;padding:10px 14px;background:#fbfdfc}.plot-info dt{color:#71847c;font-size:12px}.plot-info dd{margin:0;color:#203f34;font-size:13px;font-weight:650;text-align:right}.plot-info dd.low{color:#b84f4f}.plot-info dd small{display:block;margin-top:3px;color:#8e9d96;font-size:10px;font-weight:400}@media(max-width:760px){.plot-info dl{grid-template-columns:1fr}.plot-info dl div{border-bottom:1px solid #edf2ef}.plot-info dl div:last-child{border-bottom:0}}</style>
