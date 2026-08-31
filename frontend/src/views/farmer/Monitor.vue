<script setup>
import { computed } from 'vue'
import { useFarmerStore } from '@/stores/farmer'

const store = useFarmerStore()
const plot = computed(() => store.currentPlot)
</script>
<template>
  <div class="farmer-page">
    <template v-if="plot">
      <el-alert v-if="plot.dataState !== 'realtime'" title="当前数据并非实时数据" description="该设备数据更新时间较早，请检查网络和设备连接。" type="warning" show-icon :closable="false" class="notice" />
      <section class="farmer-stat-grid monitor-stat-grid">
        <div class="farmer-stat"><div class="stat-symbol orange"><el-icon><Sunny /></el-icon></div><div><label>环境温度</label><strong>{{ plot.temperature ?? '-' }}℃</strong><small>{{ plot.dataState === 'realtime' ? '实时数据' : '最近数据' }} · {{ plot.updateTime?.slice(11) || '暂无时间' }}</small></div></div>
        <div class="farmer-stat"><div class="stat-symbol blue"><el-icon><Drizzling /></el-icon></div><div><label>土壤湿度</label><strong>{{ plot.humidity }}%</strong><small :class="{low:plot.humidity < plot.threshold}">{{ plot.humidity < plot.threshold ? '低于' : '高于' }}阈值 {{ plot.threshold }}%</small></div></div>
        <div class="farmer-stat"><div class="stat-symbol"><el-icon><SwitchButton /></el-icon></div><div><label>灌溉状态</label><strong>{{ plot.irrigating ? '灌溉中' : '未灌溉' }}</strong><small>{{ plot.valveId }}</small></div></div>
        <div class="farmer-stat"><div :class="['stat-symbol',plot.deviceOnline?'':'red']"><el-icon><Connection /></el-icon></div><div><label>通信状态</label><strong>{{ plot.deviceOnline ? '全部在线' : `${plot.onlineDeviceCount ?? 0}/${plot.deviceCount ?? Object.keys(plot.devices || {}).length} 在线` }}</strong><small>最近心跳 {{ plot.lastHeartbeat?.slice(11) || '暂无' }}</small></div></div>
        <div class="farmer-stat"><div class="stat-symbol"><el-icon><VideoPlay /></el-icon></div><div><label>采集状态</label><strong>{{ plot.runningDeviceCount === plot.deviceCount && plot.deviceCount ? '全部运行' : plot.runningDeviceCount ? `${plot.runningDeviceCount}/${plot.deviceCount} 运行` : '全部停止' }}</strong><small>{{ plot.deviceOnline && !plot.runningDeviceCount ? '在线 · 已停止采集' : '由设备开关状态决定' }}</small></div></div>
      </section>
    </template>
  </div>
</template>
<style scoped>
.monitor-stat-grid{grid-template-columns:repeat(5,minmax(0,1fr))}
@media(max-width:1280px){.monitor-stat-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.monitor-stat-grid{grid-template-columns:1fr}}
</style>
<style scoped>.notice{margin:4px 0 18px;border-radius:12px}.low{color:#c45353!important}</style>
