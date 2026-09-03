<script setup>
import { computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import { usePlatformStore } from '@/stores/platform'
import { useUserStore } from '@/stores/user'
const platformStore = usePlatformStore()
const userStore = useUserStore()
onMounted(() => platformStore.loadData().catch(() => ElMessage.error(platformStore.loadError || '农场数据加载失败')))
const menu = [
  { label: '地块总览', path: '/farm/dashboard', icon: 'DataLine' },
  { label: '设备监测与管理', path: '/farm/device-monitoring-management', icon: 'Monitor' },
  { label: '告警日志', path: '/farm/alerts', icon: 'Bell' },
  { label: '生产档案', path: '/farm/records', icon: 'Document' },
  { label: '年度生产管理计划', path: '/farm/production', icon: 'Calendar' },
  { label: '下一年度管理计划', path: '/farm/cycle-draft', icon: 'EditPen' },
]
const farmIds = computed(() => {
  const scoped = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
  return scoped.length ? scoped : platformStore.farms.map((farm) => String(farm.farmId))
})
const contextOptions = computed(() => platformStore.farms.filter((farm) => farmIds.value.includes(String(farm.farmId))).map((farm) => ({ value: String(farm.farmId), label: `${farm.farmName || farm.name}${farm.city ? ` · ${farm.city}` : ''}` })))
const currentFarmId = computed(() => contextOptions.value.some((farm) => farm.value === String(platformStore.selectedFarmId)) ? String(platformStore.selectedFarmId) : contextOptions.value[0]?.value || '')
const currentFarm = computed(() => platformStore.farms.find((farm) => String(farm.farmId) === currentFarmId.value))
const contextLabel = computed(() => currentFarm.value?.farmName || currentFarm.value?.name || '暂无可用农场')
const scopedDevices = computed(() => platformStore.devices.filter((device) => String(device.farmId) === currentFarmId.value))
const scopedPlotIds = computed(() => platformStore.plots.filter((plot) => String(plot.farmId) === currentFarmId.value).map((plot) => plot.plotNo))
const hasUnhandledAlert = computed(() => platformStore.alerts.some((alert) => scopedPlotIds.value.includes(alert.plotId) && alert.status === '未处理'))
const contextStatus = computed(() => scopedDevices.value.some((device) => ['离线', '异常'].includes(device.status)) ? '存在离线设备' : hasUnhandledAlert.value ? '存在未处理告警' : '运行正常')
watch(contextOptions, (options) => {
  if (options.length && !options.some((farm) => farm.value === String(platformStore.selectedFarmId))) platformStore.selectFarm(options[0].value)
}, { immediate: true })
</script>
<template><AppShell title="橙心如意" subtitle="智慧农业管理平台" :menu="menu" :context-label="contextLabel" :context-options="contextOptions" :context-value="currentFarmId" :context-status="contextStatus" :context-status-tone="contextStatus === '运行正常' ? 'success' : 'warning'" accent="#1f7a5b" @context-change="platformStore.selectFarm" /></template>
