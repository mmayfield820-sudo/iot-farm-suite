<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'
import { formatDateTime } from '@/utils/dataAdapters'

const store = useFarmerStore()
const userStore = useUserStore()
const route = useRoute()
const control = reactive({ loading: false, state: 'idle', message: '请选择操作后确认下发。' })
const activeCommand = ref(null)
const selectedAction = ref('open')
const plannedDuration = ref(20)
const plot = computed(() => store.currentPlot)
const controlDevice = computed(() => plot.value?.devices?.irrigation || null)
const controlOnline = computed(() => Boolean(controlDevice.value && (controlDevice.value.online ?? plot.value?.deviceOnline)))
const records = computed(() => store.visibleRecords.filter((item) => item.plotId === plot.value?.plotId))
const suggestedEntry = computed(() => route.query.source === 'recommendation' && typeof route.query.suggestedMinutes === 'string')
const durationOptions = computed(() => {
  if (!plot.value) return []
  const limit = plot.value.irrigationDuration ?? plot.value.maxDuration ?? 30
  const values = [5, 10, 15, 20, 30, 45, 60, 90, 120, 180].filter((value) => value <= limit)
  if (!values.includes(limit)) values.push(limit)
  return [...new Set(values)].sort((a, b) => a - b)
})
const commandDisabled = computed(() => {
  if (!userStore.can('irrigation_record', 'control')) return true
  if (!controlOnline.value) return true
  return selectedAction.value === 'open' ? plot.value.irrigating : !plot.value.irrigating
})
const commandLabel = computed(() => ({ idle: '等待操作', sending: '正在下发', executing: '等待设备响应', success: '设备已确认', failed: '执行失败' })[control.state])
const formatTimestamp = (value) => formatDateTime(value, '-')

watch(
  () => plot.value?.plotId,
  () => {
    if (!plot.value) return
    selectedAction.value = plot.value.irrigating ? 'close' : 'open'
    const maximum = plot.value.irrigationDuration ?? plot.value.maxDuration ?? 30
    const suggestedMinutes = Number(route.query.suggestedMinutes)
    plannedDuration.value = route.query.plotId === plot.value.plotId && Number.isFinite(suggestedMinutes) && suggestedMinutes > 0
      ? Math.min(suggestedMinutes, maximum)
      : Math.min(20, maximum)
    control.state = 'idle'
    control.message = '请选择操作后确认下发。'
  },
  { immediate: true },
)
watch(
  [() => route.query.plotId, () => store.accessiblePlots.length],
  ([plotId]) => {
    if (typeof plotId === 'string' && store.accessiblePlots.some((item) => item.plotId === plotId)) store.selectPlot(plotId)
  },
  { immediate: true },
)

async function execute(action) {
  const verb = action === 'open' ? '开启' : '关闭'
  let commandCompleted = false
  if (!controlDevice.value) return ElMessage.error('当前地块未绑定灌溉控制器')
  if (!controlOnline.value) return ElMessage.error('灌溉控制器离线，禁止远程控制')
  try {
    await ElMessageBox.confirm(
      `目标地块：${plot.value.plotName}\n控制设备：${controlDevice.value.deviceNo}\n当前湿度：${plot.value.humidity}%\n计划时长：${action === 'open' ? `${plannedDuration.value} 分钟` : '立即关闭'}\n\n确认${verb}灌溉吗？`,
      `二次确认：${verb}灌溉`,
      { type: action === 'open' ? 'warning' : 'info', confirmButtonText: `确认${verb}`, cancelButtonText: '取消' },
    )
    control.loading = true
    activeCommand.value = store.beginCommand(plot.value.plotId, action)
    control.state = 'sending'
    control.message = `正在下发${verb}灌溉指令…`
    const submitted = await store.sendControl(activeCommand.value)
    control.state = 'executing'
    control.message = '指令已下发，正在等待设备响应…'
    const response = await store.waitCommandResult(submitted.commandId)
    const result = ['success', '成功'].includes(response?.result || response?.status) ? 'success' : response?.status === 'timeout' ? 'timeout' : 'failed'
    store.completeCommand(activeCommand.value.commandId, result, '手动')
    commandCompleted = true
    if (result !== 'success') {
      control.state = 'failed'
      control.message = response?.message || (result === 'timeout' ? '设备未在规定时间内响应' : '设备未能执行该命令')
      ElMessage.error(control.message)
      return
    }
    control.state = 'success'
    control.message = `${verb}命令已由设备确认执行`
    selectedAction.value = action === 'open' ? 'close' : 'open'
    ElMessage.success(`${verb}命令执行成功`)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      if (activeCommand.value && !commandCompleted) store.completeCommand(activeCommand.value.commandId, 'failed', '用户')
      control.state = 'failed'
      control.message = error?.message || '命令执行失败，请稍后重试'
    }
  } finally {
    control.loading = false
  }
}
</script>

<template>
  <div class="farmer-page irrigation-page">
    <div class="page-head">
      <div><h1 class="page-title">智慧灌溉</h1><p class="page-subtitle">确认后才会向设备下发指令，执行结果会保留在灌溉记录中。</p></div>
      <div class="page-actions"><div class="filter-control plot-filter"><span class="filter-label"><el-icon><Location /></el-icon> 当前地块</span><el-select class="plot-select" size="large" :model-value="store.selectedPlotId" @change="store.selectPlot"><el-option v-for="item in store.accessiblePlots" :key="item.plotId" :label="`${item.farmName} · ${item.plotName}`" :value="item.plotId" /></el-select></div></div>
    </div>

    <template v-if="plot">
      <section class="content-panel irrigation-control">
        <div class="section-head"><div><h3>灌溉控制</h3><p>{{ controlDevice?.deviceNo || '未绑定灌溉控制器' }}</p></div><span :class="['status-pill', controlOnline ? '' : 'danger']">{{ controlOnline ? '控制器在线' : '控制器不可用' }}</span></div>
        <div class="control-summary"><div><span>当前湿度</span><strong>{{ plot.humidity }}%</strong><small>参考阈值 {{ plot.threshold }}%</small></div><div><span>当前状态</span><strong>{{ plot.irrigating ? '灌溉中' : '未灌溉' }}</strong><small>单次上限 {{ plot.irrigationDuration ?? plot.maxDuration }} 分钟</small></div><div><span>最近灌溉</span><strong>{{ plot.lastIrrigation ? formatTimestamp(plot.lastIrrigation) : '暂无记录' }}</strong><small>仅可操作授权地块</small></div></div>
        <el-alert v-if="suggestedEntry" title="已按首页建议预填地块和灌溉时长" type="success" :closable="false" show-icon />
        <el-alert v-if="!controlOnline" title="灌溉控制器离线或未绑定，无法远程控制" description="请检查设备绑定状态和最后心跳。" type="error" :closable="false" show-icon />
        <div class="command-form">
          <div class="action-choice" role="group" aria-label="灌溉操作"><button :class="{ active: selectedAction === 'open' }" @click="selectedAction = 'open'">开启灌溉</button><button :class="{ active: selectedAction === 'close' }" @click="selectedAction = 'close'">关闭灌溉</button></div>
          <label class="duration-field"><span>预计时长</span><el-select v-model="plannedDuration" :disabled="selectedAction === 'close'"><el-option v-for="minutes in durationOptions" :key="minutes" :label="`${minutes} 分钟`" :value="minutes" /></el-select></label>
          <el-button type="success" size="large" :loading="control.loading" :disabled="commandDisabled" @click="execute(selectedAction)">{{ selectedAction === 'open' ? '确认并开启灌溉' : '确认并关闭灌溉' }}</el-button>
        </div>
        <div v-if="control.state !== 'idle'" :class="['command-feedback', control.state]"><span :class="['feedback-dot', control.state]"></span><strong>{{ commandLabel }}</strong><p>{{ control.message }}</p></div>
      </section>

      <section class="content-panel record-panel">
        <div class="section-head"><div><h3>灌溉执行记录</h3><p>查看当前地块的操作人、执行时间与结果。</p></div></div>
        <el-table :data="records" class="compact-table">
          <el-table-column label="开始时间" min-width="165"><template #default="scope">{{ formatTimestamp(scope.row.startTime) }}</template></el-table-column>
          <el-table-column label="结束时间" min-width="165"><template #default="scope">{{ scope.row.endTime ? formatTimestamp(scope.row.endTime) : '进行中' }}</template></el-table-column>
          <el-table-column prop="operationType" label="操作" width="80" />
          <el-table-column prop="duration" label="时长" width="90" />
          <el-table-column prop="operator" label="执行人" width="100" />
          <el-table-column prop="status" label="状态" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === '失败' ? 'danger' : scope.row.status === '进行中' ? 'info' : '']">{{ scope.row.status }}</span></template></el-table-column>
        </el-table>
        <el-empty v-if="!records.length" :image-size="58" description="暂无灌溉记录" />
      </section>
    </template>
  </div>
</template>

<style scoped>
.irrigation-control{margin-bottom:18px}.control-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin-bottom:18px;border:1px solid #e6eee9;border-radius:8px;overflow:hidden}.control-summary>div{padding:13px 15px;background:#fbfdfc}.control-summary span,.control-summary strong,.control-summary small{display:block}.control-summary span{color:#84938d;font-size:11px}.control-summary strong{margin:5px 0;color:#29483c;font-size:17px;line-height:1.25}.control-summary small{overflow:hidden;color:#9ba7a2;font-size:10px;text-overflow:ellipsis;white-space:nowrap}.irrigation-control>.el-alert{margin-bottom:12px}.command-form{display:grid;grid-template-columns:minmax(230px,1fr) 180px auto;align-items:end;gap:14px;margin-top:18px;padding-top:18px;border-top:1px solid #edf2ef}.action-choice{display:grid;grid-template-columns:1fr 1fr;padding:3px;border:1px solid #dce9e3;border-radius:8px;background:#f4f8f6}.action-choice button{height:36px;border:0;border-radius:6px;color:#647a70;background:transparent;font-size:13px;cursor:pointer}.action-choice button.active{color:#fff;background:#277e5b;box-shadow:0 2px 6px rgba(30,107,76,.16)}.duration-field{display:grid;gap:6px}.duration-field>span{color:#5d7369;font-size:12px;font-weight:650}.command-form>.el-button{min-width:174px}.command-feedback{display:flex;align-items:center;gap:8px;margin-top:16px;padding:11px 13px;border-radius:8px;color:#60776c;background:#f4f8f6;font-size:12px}.command-feedback strong{font-size:12px}.command-feedback p{margin:0;color:#73867d}.feedback-dot{width:8px;height:8px;flex:0 0 8px;border-radius:50%;background:#93a59c}.feedback-dot.sending,.feedback-dot.executing{background:#d69439}.feedback-dot.success{background:#38a06f}.feedback-dot.failed{background:#c35a5a}.record-panel{margin-top:18px}@media(max-width:850px){.command-form{grid-template-columns:1fr 180px}.command-form>.el-button{grid-column:1/-1}}@media(max-width:620px){.control-summary{grid-template-columns:1fr}.control-summary>div{border-bottom:1px solid #edf2ef}.control-summary>div:last-child{border-bottom:0}.command-form{grid-template-columns:1fr}.command-form>.el-button{grid-column:auto;width:100%}.command-feedback{align-items:flex-start;flex-wrap:wrap}.command-feedback p{width:100%;margin-left:16px}}
</style>
