<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'

const store = useFarmerStore()
const userStore = useUserStore()
const control = reactive({ loading: false, state: 'idle', message: '等待操作' })
const activeCommand = ref(null)
const selectedAction = ref('open')
const plannedDuration = ref(20)
const plot = computed(() => store.currentPlot)
const weather = computed(() => store.weather || { rainProbability: 0 })
const controlDevice = computed(() => plot.value?.devices?.irrigation || null)
const controlOnline = computed(() => Boolean(controlDevice.value && (controlDevice.value.online ?? plot.value?.deviceOnline)))
const records = computed(() => store.visibleRecords.filter((item) => item.plotId === plot.value?.plotId))
const commandLogs = computed(() => store.commandLogs.filter((item) => item.plotId === plot.value?.plotId))

const advice = computed(() => {
  if (!plot.value) return {}
  const dry = plot.value.humidity < plot.value.threshold
  return {
    action: dry && weather.value.rainProbability < 40 ? '建议进行短时灌溉' : plot.value.irrigating ? '当前正在灌溉' : '暂不建议灌溉',
    risk: dry ? '中' : '低',
    duration: Math.min(20, plot.value.irrigationDuration ?? plot.value.maxDuration ?? 30),
    evidence: [
      `当前湿度 ${plot.value.humidity}%${dry ? '低于' : '高于'}阈值 ${plot.value.threshold}%`,
      store.serviceStatus.weather ? `未来 24 小时降雨概率 ${weather.value.rainProbability}%` : '天气服务不可用，本次建议未使用天气数据',
      `灌溉控制器${controlOnline.value ? '在线，可以接收控制指令' : '离线或未绑定，禁止远程控制'}`,
      `最近一次灌溉：${plot.value.lastIrrigation || '暂无记录'}`,
    ],
  }
})

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

const humidityAngle = computed(() => `${Math.min(100, Math.max(0, plot.value?.humidity || 0)) * 3.6}deg`)
const progressSteps = ['指令下发', '设备接收', '执行反馈', '完成']
const currentStep = computed(() => ({ idle: -1, sending: 0, executing: 1, success: 3, failed: 2 }[control.state] ?? -1))
const progressLabel = computed(() => ({ idle: '等待操作', sending: '正在下发', executing: '设备执行中', success: '执行成功', failed: '执行失败' }[control.state]))

function progressState(index) {
  if (control.state === 'failed' && index === currentStep.value) return 'error'
  if (index < currentStep.value || control.state === 'success') return 'done'
  if (index === currentStep.value) return 'active'
  return 'pending'
}

watch(
  () => plot.value?.plotId,
  () => {
    if (!plot.value) return
    selectedAction.value = plot.value.irrigating ? 'close' : 'open'
    plannedDuration.value = Math.min(20, plot.value.irrigationDuration ?? plot.value.maxDuration ?? 30)
    control.state = 'idle'
    control.message = '等待操作'
  },
  { immediate: true },
)

async function execute(action) {
  const verb = action === 'open' ? '开启' : '关闭'
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
    control.message = `指令 ${activeCommand.value.commandId} 下发中，等待设备结果回传…`
    await new Promise((resolve) => setTimeout(resolve, 650))
    control.state = 'executing'
    control.message = '等待后端与设备返回执行结果…'
    const response = await store.sendControl(activeCommand.value, plannedDuration.value)
    const result = ['success', '成功', 'accepted'].includes(response?.result || response?.status || 'success') ? 'success' : 'failed'
    store.completeCommand(activeCommand.value.commandId, result, '手动')
    if (result !== 'success') throw new Error(response?.message || '设备返回执行失败')
    control.state = 'success'
    control.message = `设备已确认，${verb}灌溉执行成功`
    selectedAction.value = action === 'open' ? 'close' : 'open'
    ElMessage.success(`${verb}灌溉成功`)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      if (activeCommand.value) store.completeCommand(activeCommand.value.commandId, 'failed', '用户')
      control.state = 'failed'
      control.message = '指令执行失败，请检查设备后重试'
    }
  } finally {
    control.loading = false
  }
}
</script>

<template>
  <div class="farmer-page irrigation-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">智慧灌溉</h1>
        <p class="page-subtitle">依据实时农情和天气生成可解释建议，控制操作必须二次确认。</p>
      </div>
      <div class="page-actions">
        <div class="filter-control plot-filter">
          <span class="filter-label"><el-icon><Location /></el-icon> 当前地块</span>
          <el-select class="plot-select" size="large" :model-value="store.selectedPlotId" @change="store.selectPlot">
            <el-option v-for="item in store.accessiblePlots" :key="item.plotId" :label="`${item.farmName} · ${item.plotName}`" :value="item.plotId" />
          </el-select>
        </div>
      </div>
    </div>

    <template v-if="plot">
      <section class="irrigation-main">
        <div class="content-panel advice-card">
          <div class="advice-top">
            <div class="advice-icon"><el-icon><MagicStick /></el-icon></div>
            <div><span>智能建议 · 风险等级 {{ advice.risk }}</span><h2>{{ advice.action }}</h2><p>建议灌溉时长 {{ advice.duration }} 分钟</p></div>
          </div>
          <div class="evidence-list">
            <div v-for="item in advice.evidence" :key="item" class="evidence-item"><el-icon><CircleCheck /></el-icon><span>{{ item }}</span></div>
          </div>
          <el-alert v-if="!store.serviceStatus.weather" title="天气数据暂不可用，当前建议仅依据农田数据生成" type="warning" show-icon :closable="false" />
        </div>

        <div class="content-panel control-console">
          <div class="console-head">
            <div><span>控制设备</span><strong>{{ controlDevice?.deviceNo || '未绑定' }}</strong><small>单次灌溉配置 {{ plot.irrigationDuration ?? plot.maxDuration }} 分钟</small></div>
            <span :class="['status-pill', controlOnline ? '' : 'danger']">{{ controlOnline ? '控制器在线' : '控制器不可用' }}</span>
          </div>

          <div class="console-body">
            <aside class="status-column">
              <div class="humidity-card">
                <span>当前土壤湿度</span>
                <div class="humidity-gauge" :style="{ '--humidity-angle': humidityAngle }"><div><strong>{{ plot.humidity }}</strong><small>%</small></div></div>
                <em>目标阈值 {{ plot.threshold }}%</em>
              </div>
              <div class="mini-status"><span>控制器状态</span><strong :class="{ danger: !controlOnline }">{{ controlOnline ? '在线' : controlDevice ? '离线' : '未绑定' }}</strong></div>
              <div class="mini-status"><span>当前灌溉状态</span><strong>{{ plot.irrigating ? '灌溉中' : '未灌溉' }}</strong></div>
            </aside>

            <div class="switch-column">
              <h3>灌溉开关</h3>
              <div class="action-tabs">
                <button :class="{ active: selectedAction === 'open' }" @click="selectedAction = 'open'">开启</button>
                <button :class="{ active: selectedAction === 'close' }" @click="selectedAction = 'close'">关闭</button>
              </div>
              <button class="control-dial" :class="selectedAction" :aria-label="selectedAction === 'open' ? '选择开启灌溉' : '选择关闭灌溉'" @click="selectedAction = selectedAction === 'open' ? 'close' : 'open'">
                <span class="dial-marker"></span><el-icon><SwitchButton /></el-icon>
              </button>
              <div class="dial-labels"><span>开启灌溉</span><span>关闭灌溉</span></div>

              <div class="duration-row">
                <label>预计灌溉时长</label>
                <el-select v-model="plannedDuration" :disabled="selectedAction === 'close'">
                  <el-option v-for="minutes in durationOptions" :key="minutes" :label="`${minutes} 分钟`" :value="minutes" />
                </el-select>
              </div>
              <p class="duration-note">当前地块单次灌溉配置：{{ plot.irrigationDuration ?? plot.maxDuration }} 分钟</p>
              <el-button class="confirm-command" type="success" size="large" :loading="control.loading" :disabled="commandDisabled" @click="execute(selectedAction)">
                {{ selectedAction === 'open' ? '确认并开启灌溉' : '确认并关闭灌溉' }}
              </el-button>
            </div>
          </div>

          <div class="command-progress">
            <div class="progress-head"><h4>指令执行状态</h4><span :class="['progress-result', control.state]"><el-icon v-if="control.state === 'success'"><CircleCheckFilled /></el-icon><el-icon v-else-if="control.state === 'failed'"><CircleCloseFilled /></el-icon>{{ progressLabel }}</span></div>
            <div class="progress-track">
              <div v-for="(item, index) in progressSteps" :key="item" :class="['progress-step', progressState(index)]">
                <span class="progress-dot"><el-icon v-if="progressState(index) === 'done'"><Check /></el-icon><el-icon v-else-if="progressState(index) === 'error'"><Close /></el-icon></span>
                <strong>{{ item }}</strong>
              </div>
            </div>
            <p>{{ control.message }}</p>
          </div>
          <el-alert v-if="!controlOnline" title="灌溉控制器离线或未绑定，禁止远程控制" description="请先检查设备绑定、启用状态和最后心跳。" type="error" show-icon :closable="false" />
        </div>
      </section>

      <section v-if="commandLogs.length" class="content-panel command-panel">
        <div class="section-head"><div><h3>控制指令状态</h3><p>设备回传成功、失败或超时结果</p></div></div>
        <el-table :data="commandLogs" class="compact-table">
          <el-table-column prop="commandId" label="指令编号" min-width="155" />
          <el-table-column prop="deviceId" label="设备编号" min-width="120" />
          <el-table-column prop="action" label="动作" min-width="120" />
          <el-table-column prop="sentAt" label="下发时间" min-width="165" />
          <el-table-column prop="resultAt" label="结果时间" min-width="165" />
          <el-table-column prop="status" label="状态" width="100"><template #default="scope"><span :class="['status-pill', scope.row.status === '失败' || scope.row.status === '超时' ? 'danger' : scope.row.status === '下发中' ? 'warning' : '']">{{ scope.row.status }}</span></template></el-table-column>
        </el-table>
      </section>

      <section class="content-panel record-panel">
        <div class="section-head"><div><h3>灌溉执行记录</h3><p>记录操作人、操作类型、起止时间和执行结果</p></div></div>
        <el-table :data="records" class="compact-table">
          <el-table-column prop="startTime" label="开始时间" min-width="165" />
          <el-table-column prop="endTime" label="结束时间" min-width="165"><template #default="scope">{{ scope.row.endTime || '进行中' }}</template></el-table-column>
          <el-table-column prop="operationType" label="操作" width="80" />
          <el-table-column prop="duration" label="计划/实际时长" min-width="120" />
          <el-table-column prop="operator" label="操作人" width="100" />
          <el-table-column prop="source" label="来源" min-width="120" />
          <el-table-column prop="status" label="执行状态" width="110"><template #default="scope"><span :class="['status-pill', scope.row.status === '失败' ? 'danger' : scope.row.status === '进行中' ? 'info' : '']">{{ scope.row.status }}</span></template></el-table-column>
        </el-table>
      </section>
    </template>
  </div>
</template>

<style scoped>
.irrigation-main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-bottom:18px}.advice-card{background:linear-gradient(135deg,#eff9f4,#fff)}.advice-top{display:flex;align-items:center;gap:14px}.advice-icon{width:52px;height:52px;display:grid;place-items:center;flex:0 0 52px;border-radius:16px;color:#247b58;background:#dcf2e7;font-size:25px}.advice-top span{color:#408064;font-size:12px;font-weight:650}.advice-top h2{margin:6px 0 4px;font-size:20px}.advice-top p{margin:0;color:#81918b;font-size:12px}.control-console{padding:18px 20px}.console-head{display:flex;align-items:flex-start;justify-content:space-between;gap:15px;padding-bottom:14px;border-bottom:1px solid #e5eee9}.console-head div>span,.console-head div>strong,.console-head div>small{display:block}.console-head div>span{color:#7f9189;font-size:11px}.console-head div>strong{margin-top:3px;color:#25483a;font-size:19px}.console-head div>small{margin-top:4px;color:#91a098;font-size:11px}.console-body{display:grid;grid-template-columns:190px minmax(0,1fr);gap:22px;padding-top:16px}.status-column{display:grid;gap:10px;padding:12px;border-radius:17px;background:linear-gradient(180deg,#257655,#1b5b43)}.humidity-card,.mini-status{border-radius:12px;background:#f9fcfa}.humidity-card{padding:13px;text-align:center}.humidity-card>span{display:block;color:#4e665d;font-size:11px;font-weight:650}.humidity-gauge{width:92px;height:92px;display:grid;place-items:center;margin:10px auto 6px;border-radius:50%;background:conic-gradient(#2c9368 0 var(--humidity-angle),#e8eee9 var(--humidity-angle) 360deg)}.humidity-gauge>div{width:68px;height:68px;display:grid;place-content:center;border-radius:50%;background:#fff}.humidity-gauge strong{font-size:24px}.humidity-gauge small{font-size:11px}.humidity-card em{color:#8a9992;font-size:10px;font-style:normal}.mini-status{padding:12px}.mini-status span,.mini-status strong{display:block}.mini-status span{color:#7e8f88;font-size:10px}.mini-status strong{margin-top:5px;color:#24533f;font-size:15px}.mini-status strong.danger{color:#c45353}.switch-column{min-width:0}.switch-column h3{margin:0 0 8px;color:#29473d}.action-tabs{display:flex;justify-content:center;gap:8px}.action-tabs button{padding:5px 14px;border:0;border-radius:14px;color:#83918c;background:#f0f4f2;cursor:pointer}.action-tabs button.active{color:#fff;background:#2e8b63}.control-dial{width:142px;height:142px;position:relative;display:grid;place-items:center;margin:10px auto 4px;border:12px solid #eef1ef;border-radius:50%;color:#fff;background:linear-gradient(145deg,#a9b1ad,#737c78);box-shadow:inset 0 0 0 3px #fff,0 8px 18px rgba(28,71,54,.2);font-size:36px;cursor:pointer}.control-dial::before{position:absolute;inset:-12px;content:'';border-radius:50%;border:8px solid transparent;border-top-color:#2f9368;transform:rotate(-45deg)}.control-dial.close::before{border-top-color:#d8894b;transform:rotate(135deg)}.dial-marker{width:8px;height:31px;position:absolute;top:12px;border-radius:5px;background:#fff;transform-origin:4px 47px;transition:.25s}.control-dial.open .dial-marker{transform:rotate(-46deg)}.control-dial.close .dial-marker{transform:rotate(46deg)}.dial-labels{display:flex;justify-content:space-around;color:#5f716a;font-size:11px}.duration-row{display:grid;grid-template-columns:125px 1fr;align-items:center;gap:10px;margin-top:14px}.duration-row label{color:#334f45;font-size:12px;font-weight:650}.duration-row .el-select{width:100%}.duration-note{margin:7px 0 10px;color:#9a8874;font-size:10px;text-align:right}.confirm-command{width:100%;border-radius:12px}.command-progress{margin-top:14px;padding:13px 15px;border-radius:12px;background:#f6faf8}.progress-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.progress-head h4{margin:0;color:#334f45;font-size:12px}.progress-result{display:flex;align-items:center;gap:5px;color:#7c8c85;font-size:11px;font-weight:650}.progress-result.sending,.progress-result.executing{color:#bd7b2f}.progress-result.success{color:#27875e}.progress-result.failed{color:#c45353}.progress-track{display:grid;grid-template-columns:repeat(4,1fr);margin-top:14px}.progress-step{position:relative;display:flex;align-items:center;justify-content:center;padding-top:20px;color:#9aa7a2}.progress-step::before{height:3px;position:absolute;top:6px;left:0;right:0;content:'';background:#dfe7e3}.progress-step:first-child::before{left:50%}.progress-step:last-child::before{right:50%}.progress-dot{width:13px;height:13px;position:absolute;top:1px;z-index:1;display:grid;place-items:center;border:2px solid #cbd6d1;border-radius:50%;background:#fff;font-size:8px}.progress-step strong{font-size:10px}.progress-step.done::before,.progress-step.active::before{background:#35a273}.progress-step.done .progress-dot{border-color:#35a273;color:#fff;background:#35a273}.progress-step.active{color:#a86b22}.progress-step.active .progress-dot{border-color:#e09a44;background:#fff3df;box-shadow:0 0 0 4px #fff5e8}.progress-step.error{color:#c45353}.progress-step.error .progress-dot{border-color:#cf5d5d;color:#fff;background:#cf5d5d}.command-progress>p{margin:11px 0 0;color:#6f8179;font-size:10px;text-align:center}.command-panel,.record-panel{margin-top:18px}@media(max-width:1200px){.irrigation-main{grid-template-columns:1fr}.console-body{grid-template-columns:210px minmax(0,1fr)}}@media(max-width:700px){.console-body{grid-template-columns:1fr}.status-column{grid-template-columns:1fr 1fr}.humidity-card{grid-row:span 2}.duration-row{grid-template-columns:1fr}.irrigation-main{display:block}.advice-card{margin-bottom:18px}}@media(max-width:480px){.status-column{grid-template-columns:1fr}.humidity-card{grid-row:auto}.control-dial{width:126px;height:126px}}
</style>
