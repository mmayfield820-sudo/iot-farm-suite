<script setup>
import { computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import { usePlatformStore } from '@/stores/platform'
import { useUserStore } from '@/stores/user'
const platformStore = usePlatformStore()
const userStore = useUserStore()
onMounted(() => platformStore.loadData().catch(() => ElMessage.error(platformStore.loadError || '农场数据加载失败')))
const menu = [
  { label: '多地块总览', path: '/farm/dashboard', icon: 'DataLine' },
  { label: '设备状态', path: '/farm/status', icon: 'Monitor' },
  { label: '设备管理', path: '/farm/devices', icon: 'Cpu' },
  { label: '告警日志', path: '/farm/alerts', icon: 'Bell' },
]
const farmIds = computed(() => {
  const scoped = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
  return scoped.length ? scoped : platformStore.farms.map((farm) => String(farm.farmId))
})
const contextLabel = computed(() => {
  const farms = platformStore.farms.filter((farm) => farmIds.value.includes(String(farm.farmId)))
  return farms.length === 1 ? farms[0].farmName || farms[0].name : `已授权 ${farms.length || farmIds.value.length} 个农场`
})
const scopedDevices = computed(() => platformStore.devices.filter((device) => farmIds.value.includes(String(device.farmId))))
const scopedPlotIds = computed(() => platformStore.plots.filter((plot) => farmIds.value.includes(String(plot.farmId))).map((plot) => plot.plotNo))
const hasUnhandledAlert = computed(() => platformStore.alerts.some((alert) => scopedPlotIds.value.includes(alert.plotId) && alert.status === '未处理'))
const contextStatus = computed(() => scopedDevices.value.some((device) => ['离线', '异常'].includes(device.status)) ? '存在离线设备' : hasUnhandledAlert.value ? '存在未处理告警' : '运行正常')
</script>
<template><AppShell title="智慧农业平台" subtitle="FARM MANAGEMENT" :menu="menu" :context-label="contextLabel" :context-status="contextStatus" :context-status-tone="contextStatus === '运行正常' ? 'success' : 'warning'" accent="#1f7a5b" /></template>
