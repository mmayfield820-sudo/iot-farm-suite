<script setup>
import { computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import { usePlatformStore } from '@/stores/platform'
import { useFarmAdminStore } from '@/stores/farmAdmin'
const platformStore = usePlatformStore()
const farmAdminStore = useFarmAdminStore()
onMounted(() => platformStore.loadData().catch(() => ElMessage.error(platformStore.loadError || '农场数据加载失败')))
const menu = [
  { label: '多地块总览', path: '/farm/dashboard', icon: 'DataLine' },
  { label: '设备状态', path: '/farm/status', icon: 'Monitor' },
  { label: '设备管理', path: '/farm/devices', icon: 'Cpu' },
  { label: '告警日志', path: '/farm/alerts', icon: 'Bell' },
]
const contextLabel = computed(() => farmAdminStore.selectedFarmLabel)
const scopedDevices = computed(() => farmAdminStore.visibleDevices)
const scopedPlotIds = computed(() => farmAdminStore.visiblePlots.map((plot) => plot.plotNo))
const hasUnhandledAlert = computed(() => platformStore.alerts.some((alert) => scopedPlotIds.value.includes(alert.plotId) && alert.status === '未处理'))
const contextStatus = computed(() => scopedDevices.value.some((device) => ['离线', '异常'].includes(device.status)) ? '存在离线设备' : hasUnhandledAlert.value ? '存在未处理告警' : '运行正常')
</script>
<template>
  <AppShell title="智慧农业平台" subtitle="FARM MANAGEMENT" :menu="menu" :context-label="contextLabel" :context-status="contextStatus" :context-status-tone="contextStatus === '运行正常' ? 'success' : 'warning'" accent="#1f7a5b">
    <template #context>
      <div class="farm-context">
        <span class="farm-dot"></span>
        <el-select
          v-if="farmAdminStore.accessibleFarms.length > 1"
          :model-value="farmAdminStore.selectedFarmId"
          class="farm-switch"
          size="small"
          aria-label="切换当前农场"
          @change="farmAdminStore.selectFarm"
        >
          <el-option :label="`全部农场（${farmAdminStore.accessibleFarms.length}）`" value="all" />
          <el-option v-for="farm in farmAdminStore.accessibleFarms" :key="farm.farmId" :label="farm.farmName || farm.name" :value="String(farm.farmId)" />
        </el-select>
        <span v-else class="single-farm-name">{{ contextLabel }}</span>
        <span :class="['context-state', contextStatus === '运行正常' ? 'success' : 'warning']">{{ contextStatus }}</span>
      </div>
    </template>
  </AppShell>
</template>

<style scoped>
.farm-context{display:flex;align-items:center;gap:8px}.farm-dot{width:8px;height:8px;flex:0 0 8px;border-radius:50%;background:#39ae75;box-shadow:0 0 0 4px #dff4e9}.farm-switch{width:200px}.farm-switch :deep(.el-select__wrapper){border:0;background:#f4f9f6;box-shadow:0 0 0 1px #dce9e3 inset}.single-farm-name{color:#405e53;font-weight:600}.context-state{padding:4px 8px;border-radius:9px;font-size:12px}.context-state.success{color:#2a875f;background:#e9f7f0}.context-state.warning{color:#a46823;background:#fff3df}
</style>
