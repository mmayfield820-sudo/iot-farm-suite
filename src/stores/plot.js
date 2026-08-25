import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const usePlotStore = defineStore('plot', () => {
  const plots = ref([])
  const loading = ref(false)

  const onlineCount = computed(() => plots.value.reduce((sum, plot) => sum + (plot.onlineDeviceCount ?? (plot.deviceOnline ? 1 : 0)), 0))
  const offlineCount = computed(() => plots.value.filter(p => !p.deviceOnline).length)
  const alertCount = computed(() => plots.value.filter(p => p.status === 'alert').length)
  const irrigatingCount = computed(() => plots.value.filter(p => p.irrigating).length)
  const unhandledAlertCount = computed(() => 
    plots.value.reduce((sum, p) => sum + (p.unhandledAlerts || 0), 0)
  )

  const setPlots = (data) => {
    plots.value = data
  }

  const updatePlot = (plotId, updates) => {
    const idx = plots.value.findIndex(p => p.plotId === plotId)
    if (idx !== -1) {
      plots.value[idx] = { ...plots.value[idx], ...updates }
    }
  }

  const getPlotById = (plotId) => plots.value.find(p => p.plotId === plotId)

  return {
    plots, loading,
    onlineCount, offlineCount, alertCount, irrigatingCount, unhandledAlertCount,
    setPlots, updatePlot, getPlotById
  }
})
