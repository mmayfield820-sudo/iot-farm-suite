<script setup>
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import { useFarmerStore } from '@/stores/farmer'

const farmerStore = useFarmerStore()
let refreshTimer
let refreshInFlight = false

async function refreshRealtimeData() {
  if (refreshInFlight) return
  refreshInFlight = true
  try {
    await farmerStore.refreshRealtimeData()
  } finally {
    refreshInFlight = false
  }
}

onMounted(async () => {
  try {
    await farmerStore.loadFarmerData()
  } catch {
    ElMessage.error(farmerStore.loadError || '农户数据加载失败')
  }
  refreshTimer = window.setInterval(() => refreshRealtimeData().catch(() => {}), 10000)
})

onBeforeUnmount(() => window.clearInterval(refreshTimer))
const menu = [
  { label: '农场首页', path: '/farmer/dashboard', icon: 'House' }, { label: '地块管理', path: '/farmer/management', icon: 'DataAnalysis' },
  { label: '智慧灌溉', path: '/farmer/irrigation', icon: 'Drizzling' },
  { label: '告警中心', path: '/farmer/alarm', icon: 'Warning' },
  { label: 'AI 农业助手', path: '/farmer/ai', icon: 'ChatDotRound' },
]

const contextLabel = computed(() => {
  const plot = farmerStore.currentPlot
  return plot ? `${plot.farmName || '未命名农场'} · ${plot.plotName}` : '暂无可用地块'
})

const contextStatus = computed(() => {
  const plot = farmerStore.currentPlot
  if (!plot) return '暂无数据'
  if (!plot.deviceOnline) return '设备离线'
  if (plot.dataState !== 'realtime') return '数据延迟'
  if (plot.irrigating) return '灌溉中'
  if (['alert', 'dry'].includes(plot.status)) return '存在告警'
  return '运行正常'
})

const contextStatusTone = computed(() => {
  if (contextStatus.value === '设备离线') return 'danger'
  if (['数据延迟', '存在告警'].includes(contextStatus.value)) return 'warning'
  if (contextStatus.value === '灌溉中') return 'info'
  return 'success'
})
</script>
<template><AppShell title="智慧农业平台" subtitle="SMART AGRICULTURE" :menu="menu" :context-label="contextLabel" :context-status="contextStatus" :context-status-tone="contextStatusTone" /></template>
