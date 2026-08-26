import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { usePlatformStore } from '@/stores/platform'
import { useUserStore } from '@/stores/user'

const STORAGE_KEY = 'smart-agriculture-farm-admin-selected'
const ALL_FARMS = 'all'

export const useFarmAdminStore = defineStore('farmAdmin', () => {
  const platformStore = usePlatformStore()
  const userStore = useUserStore()
  const selectedFarmId = ref(localStorage.getItem(STORAGE_KEY) || ALL_FARMS)

  const accessibleFarmIds = computed(() => {
    const scoped = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
    return scoped.length ? scoped : platformStore.farms.map((farm) => String(farm.farmId))
  })

  const accessibleFarms = computed(() => platformStore.farms.filter((farm) => accessibleFarmIds.value.includes(String(farm.farmId))))

  const selectedFarmIds = computed(() => selectedFarmId.value === ALL_FARMS
    ? accessibleFarmIds.value
    : accessibleFarmIds.value.includes(String(selectedFarmId.value)) ? [String(selectedFarmId.value)] : [])

  const selectedFarm = computed(() => accessibleFarms.value.find((farm) => String(farm.farmId) === String(selectedFarmId.value)) || null)
  const selectedFarmLabel = computed(() => selectedFarmId.value === ALL_FARMS
    ? `全部农场（${accessibleFarms.value.length}）`
    : selectedFarm.value?.farmName || selectedFarm.value?.name || '未知农场')

  const visiblePlots = computed(() => platformStore.plots.filter((plot) => selectedFarmIds.value.includes(String(plot.farmId))))
  const visibleDevices = computed(() => platformStore.devices.filter((device) => selectedFarmIds.value.includes(String(device.farmId))))
  const visiblePlotIds = computed(() => visiblePlots.value.map((plot) => String(plot.plotNo || plot.plotId)))
  const visibleAlerts = computed(() => platformStore.alerts.filter((alert) => {
    if (alert.farmId) return selectedFarmIds.value.includes(String(alert.farmId))
    return visiblePlotIds.value.includes(String(alert.plotNo || alert.plotId))
  }))

  function selectFarm(farmId) {
    const next = String(farmId || ALL_FARMS)
    selectedFarmId.value = next === ALL_FARMS || accessibleFarmIds.value.includes(next) ? next : ALL_FARMS
  }

  watch(accessibleFarmIds, (farmIds) => {
    if (selectedFarmId.value !== ALL_FARMS && !farmIds.includes(String(selectedFarmId.value))) selectedFarmId.value = ALL_FARMS
  }, { immediate: true })

  watch(selectedFarmId, (farmId) => localStorage.setItem(STORAGE_KEY, String(farmId)))

  return {
    ALL_FARMS,
    selectedFarmId,
    accessibleFarmIds,
    accessibleFarms,
    selectedFarmIds,
    selectedFarm,
    selectedFarmLabel,
    visiblePlots,
    visibleDevices,
    visibleAlerts,
    selectFarm,
  }
})
