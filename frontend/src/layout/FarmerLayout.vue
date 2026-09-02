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
  refreshTimer = window.setInterval(() => refreshRealtimeData().catch(() => {}), 2000)
})

onBeforeUnmount(() => window.clearInterval(refreshTimer))
const menu = [
  { label: '农场首页', path: '/farmer/dashboard', icon: 'House' }, { label: '地块管理', path: '/farmer/management', icon: 'DataAnalysis' },
  { label: '管理计划', path: '/farmer/plan', icon: 'Notebook' },
  { label: '我的农事', path: '/farmer/tasks', icon: 'List' },
  { label: '智慧灌溉', path: '/farmer/irrigation', icon: 'Drizzling' },
  { label: '告警中心', path: '/farmer/alarm', icon: 'BellFilled' },
  { label: '小橙子·农事助手', path: '/farmer/ai', icon: 'ChatDotRound' },
]

const contextLabel = computed(() => {
  return farmerStore.currentFarm?.farmName || '暂无可用农场'
})
const contextOptions = computed(() => farmerStore.accessibleFarms.map((farm) => ({
  label: farm.farmName,
  value: farm.farmId,
})))

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
<template><AppShell class="farmer-shell" title="橙心如意" subtitle="智慧农业管理平台" :menu="menu" :context-label="contextLabel" :context-options="contextOptions" :context-value="farmerStore.currentFarm?.farmId || ''" :context-status="contextStatus" :context-status-tone="contextStatusTone" :allow-role-switch="false" @context-change="farmerStore.selectFarm" /></template>

<style scoped>
:global(.farmer-shell) { --accent: #237a43 !important; --el-color-primary: #237a43 !important; background: #faf9e8; }
:global(.farmer-shell .workspace), :global(.farmer-shell .content) { background: #faf9e8; }
:global(.farmer-shell .sidebar) { background: linear-gradient(180deg, #064d39 0%, #013f30 100%); }
:global(.farmer-shell .brand) { height: 88px; padding: 0 20px; }
:global(.farmer-shell .brand-mark) { width: 54px; height: 54px; flex-basis: 54px; padding: 0; border: 0; border-radius: 0; background: transparent; box-shadow: none; }
:global(.farmer-shell .brand-mark img) { display: block; width: 100%; height: 100%; object-fit: contain; }
:global(.farmer-shell .brand strong) { font-size: 20px; letter-spacing: 0; }
:global(.farmer-shell .brand span) { color: #dcebe4; font-size: 13px; letter-spacing: 0; }
:global(.farmer-shell .nav) { padding: 12px 12px; }
:global(.farmer-shell .nav .el-menu-item) { height: 46px; margin-bottom: 3px; border-radius: 7px; color: #e8f1ed; font-size: 14px; font-weight: 600; }
:global(.farmer-shell .nav .el-menu-item .el-icon) { font-size: 18px; }
:global(.farmer-shell .nav .el-menu-item.is-active) { background: #3e954d; }
:global(.farmer-shell .collapse-btn) { height: 58px; padding: 0 30px; color: #e1efe9; font-size: 14px; font-weight: 600; }
:global(.farmer-shell .topbar) { height: 83px; padding: 0 34px; color: #16231d; background: rgba(250, 249, 232, .78); backdrop-filter: blur(10px); }
:global(.farmer-shell .topbar > div:first-child) { color: #18251f; font-size: 16px; font-weight: 700; }
:global(.farmer-shell .farm-context-select) { width: 168px; }
:global(.farmer-shell .farm-context-select .el-select__wrapper) { background: transparent; }
:global(.farmer-shell .online) { display: none; }
:global(.farmer-shell .user-area) { gap: 14px; }
:global(.farmer-shell .font-trigger) { display: none; }
:global(.farmer-shell .notification-btn) { width: 36px; height: 36px; border: 0; border-radius: 50%; background: transparent; color: #17231e; font-size: 22px; }
:global(.farmer-shell .single-role) { color: #217746; background: #f0f7ed; font-weight: 700; }
:global(.farmer-shell .avatar) { width: 45px; height: 45px; background: #d4a43d; font-size: 17px; font-weight: 700; }
:global(.farmer-shell .display-name) { color: #15241d; font-size: 16px; font-weight: 700; }
:global(.farmer-shell .user-area .el-button) { color: #293d34; font-size: 15px; }
:global(.farmer-shell .content) { max-width: 1480px; width: 100%; padding: 28px 32px 36px; margin: 0 auto; }
:global(.farmer-shell .farmer-page) { max-width: none; }
:global(.farmer-shell .page-title) { color: #134b35; font-size: 30px !important; }
:global(.farmer-shell .page-subtitle) { margin-bottom: 24px; color: #606f69; font-size: 15px !important; }
:global(.farmer-shell .content-panel), :global(.farmer-shell .panel) { border-color: #e7ebe6; border-radius: 10px; box-shadow: 0 7px 20px rgba(24, 65, 45, .045); }
:global(.farmer-shell .farmer-stat) { min-height: 112px; border-color: #e7ebe6; border-radius: 10px; box-shadow: 0 7px 20px rgba(24, 65, 45, .045); }
:global(.farmer-shell .filter-control .plot-select .el-select__wrapper), :global(.farmer-shell .el-select__wrapper) { min-height: 42px; border-radius: 7px; }
:global(.farmer-shell .el-button--success) { --el-button-bg-color: #16733a; --el-button-border-color: #16733a; --el-button-hover-bg-color: #25854c; --el-button-hover-border-color: #25854c; }
:global(.farmer-shell .compact-table.el-table) { border: 1px solid #edf0eb; border-radius: 8px; }
:global(.farmer-shell .compact-table .el-table__header-wrapper th) { height: 46px; color: #20523d; background: #f5f8f3 !important; }
:global(.farmer-shell .compact-table .el-table__cell) { padding: 10px 0; }

@media (max-width: 900px) {
  :global(.farmer-shell .brand) { height: 82px; padding: 0; }
  :global(.farmer-shell .brand-mark) { width: 48px; height: 48px; flex-basis: 48px; }
  :global(.farmer-shell .nav) { padding: 16px 10px; }
  :global(.farmer-shell .nav .el-menu-item) { height: 52px; }
  :global(.farmer-shell .collapse-btn) { height: 62px; padding: 0; justify-content: center; }
  :global(.farmer-shell .topbar) { height: 64px; padding: 0 18px; }
  :global(.farmer-shell .content) { padding: 20px 18px 30px; }
}
</style>
