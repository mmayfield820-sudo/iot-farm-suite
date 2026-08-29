<script setup>
import { computed, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'

const store = useFarmerStore()
const userStore = useUserStore()
const plot = computed(() => store.currentPlot)
const config = reactive({ threshold: 35, irrigationDuration: 30, irrigationInterval: 60 })

watch(
  () => plot.value?.plotId,
  () => {
    if (!plot.value) return
    Object.assign(config, {
      threshold: plot.value.threshold,
      irrigationDuration: plot.value.irrigationDuration ?? plot.value.maxDuration,
      irrigationInterval: plot.value.irrigationInterval ?? 60,
    })
  },
  { immediate: true },
)

async function saveConfig() {
  if (!plot.value) return
  try {
    await store.updateThreshold(plot.value.plotId, config)
    ElMessage.success(`${plot.value.plotName}的阈值设置已保存`)
  } catch (error) { ElMessage.error(error?.response?.data?.message || error.message || '保存失败') }
}
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
      <section class="plot-config-row">
        <div class="content-panel plot-info">
          <div class="section-head"><div><h3>地块信息</h3><p>{{ plot.plotId }}</p></div></div>
          <dl>
            <div><dt>所属农场</dt><dd>{{ plot.farmName }}</dd></div>
            <div><dt>作物</dt><dd>{{ plot.cropName }} · {{ plot.cropStage }}</dd></div>
            <div><dt>位置</dt><dd>{{ plot.location }}</dd></div>
            <div><dt>传感器</dt><dd>{{ plot.sensorId }}</dd></div>
            <div><dt>最近灌溉</dt><dd>{{ plot.lastIrrigation }}</dd></div>
          </dl>
        </div>

        <div class="content-panel threshold-config">
          <div class="section-head">
            <div><h3>阈值设置</h3><p>当前设置仅对 {{ plot.plotName }} 生效</p></div>
            <span class="status-pill">独立配置</span>
          </div>
          <div class="config-fields">
            <label><span>土壤湿度阈值</span><el-input-number v-model="config.threshold" :min="10" :max="80" :step="1" controls-position="right" /><small>低于该值时触发告警（%）</small></label>
            <label><span>单次灌溉时长</span><el-input-number v-model="config.irrigationDuration" :min="1" :max="240" :step="5" controls-position="right" /><small>对应 irrigation_length_minutes（分钟）</small></label>
            <label><span>自动灌溉间隔</span><el-input-number v-model="config.irrigationInterval" :min="1" :max="1440" :step="5" controls-position="right" /><small>对应 irrigation_interval_minutes（分钟）</small></label>
          </div>
          <div class="config-footer"><span>{{ userStore.can('threshold_config', 'modify') ? '切换地块后将载入该地块自己的设置' : '当前角色没有修改阈值的权限' }}</span><el-button type="success" :disabled="!userStore.can('threshold_config', 'modify')" @click="saveConfig"><el-icon><Check /></el-icon> 保存设置</el-button></div>
        </div>
      </section>
    </template>
  </div>
</template>
<style scoped>
.monitor-stat-grid{grid-template-columns:repeat(5,minmax(0,1fr))}
@media(max-width:1280px){.monitor-stat-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.monitor-stat-grid{grid-template-columns:1fr}}
</style>
<style scoped>.notice{margin:4px 0 18px;border-radius:12px}.low{color:#c45353!important}.plot-config-row{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(430px,.9fr);gap:18px;margin-bottom:18px}.plot-info,.threshold-config{height:100%}.plot-info .section-head h3,.threshold-config .section-head h3{font-size:18px}.plot-info .section-head p{font-size:13px;font-weight:600}.plot-info dl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 16px;margin:0}.plot-info dl div{display:flex;align-items:center;justify-content:space-between;gap:14px;min-height:48px;padding:10px 14px;border-radius:10px;background:#f7faf8}.plot-info dt{color:#71847c;font-size:13px;font-weight:500}.plot-info dd{margin:0;color:#203f34;font-size:15px;font-weight:700;text-align:right}.config-fields{display:grid;gap:11px}.config-fields label{display:grid;grid-template-columns:minmax(135px,1fr) 140px;align-items:center;gap:3px 12px;padding:10px 12px;border:1px solid #e3eee8;border-radius:11px;background:#f8fbf9}.config-fields label>span{color:#315347;font-size:13px;font-weight:650}.config-fields label>small{grid-column:1;color:#8b9a94;font-size:10px}.config-fields :deep(.el-input-number){grid-column:2;grid-row:1/3;width:140px}.config-footer{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-top:14px}.config-footer>span{color:#84948d;font-size:11px}@media(max-width:1180px){.plot-config-row{grid-template-columns:1fr}}@media(max-width:760px){.plot-info dl{grid-template-columns:1fr}.config-fields label{grid-template-columns:1fr}.config-fields label>small,.config-fields :deep(.el-input-number){grid-column:1;grid-row:auto}.config-fields :deep(.el-input-number){width:100%}.config-footer{align-items:stretch;flex-direction:column}.config-footer .el-button{width:100%}}</style>
