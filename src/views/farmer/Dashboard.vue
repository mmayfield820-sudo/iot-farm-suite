<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useFarmerStore } from '@/stores/farmer'
import * as Icons from '@element-plus/icons-vue'
import FarmWheel from '@/components/FarmWheel.vue'
import TrendChart from '@/components/TrendChart.vue'
import OrchardOverview from '@/components/OrchardOverview.vue'
import tomatoBg from '@/assets/crops/tomato.png'
import pepperBg from '@/assets/crops/pepper.png'
import waterSpinachBg from '@/assets/crops/water-spinach.png'
import cucumberBg from '@/assets/crops/cucumber.png'
import lettuceBg from '@/assets/crops/lettuce.png'
import cornBg from '@/assets/crops/corn.png'
import strawberryBg from '@/assets/crops/strawberry.png'

const router = useRouter()
const store = useFarmerStore()
const plotScroller = ref(null)
const cropBackgrounds = {
  番茄: tomatoBg,
  辣椒: pepperBg,
  空心菜: waterSpinachBg,
  黄瓜: cucumberBg,
  生菜: lettuceBg,
  玉米: cornBg,
  草莓: strawberryBg,
}
const plotBackgroundStyle = (cropName) => ({
  '--plot-bg': `url(${cropBackgrounds[cropName] || tomatoBg})`,
})
const plot = computed(() => store.currentPlot)
const weather = computed(() => store.weather || { rainProbability: 0 })
const trend = computed(() => store.getTrend(plot.value?.plotId, '24h'))
const latestAlerts = computed(() => store.visibleAlerts.filter((item) => item.status === '未处理').slice(0, 3))
const onlineDeviceCount = computed(() => store.accessiblePlots.reduce((total, item) => {
  const deviceCount = Object.values(item.devices || {}).filter(Boolean).length
  return total + (item.onlineDeviceCount ?? (item.deviceOnline ? deviceCount : 0))
}, 0))
const activeAlertCount = computed(() => store.visibleAlerts.filter((item) => ['未处理', '处理中'].includes(item.status)).length)
const todayIrrigationCount = computed(() => {
  const today = new Date().toLocaleDateString('sv-SE')
  return store.visibleRecords.filter((item) => item.operationType === '开启' && item.startTime?.startsWith(today)).length
})
const dashboardStats = computed(() => [
  { label: '地块总数', value: store.accessiblePlots.length, unit: '块', icon: 'Grid', tone: 'green' },
  { label: '在线设备', value: onlineDeviceCount.value, unit: '台', icon: 'Connection', tone: 'lime' },
  { label: '当前告警', value: activeAlertCount.value, unit: '条', icon: 'BellFilled', tone: 'orange' },
  { label: '今日灌溉', value: todayIrrigationCount.value, unit: '次', icon: 'Drizzling', tone: 'blue' },
])
const recommendation = computed(() => {
  if (!plot.value) return null
  const rain = weather.value.rainProbability ?? 0
  const needsWater = plot.value.humidity < plot.value.threshold
  return {
    action: needsWater && rain < 40 ? '建议短时灌溉' : plot.value.irrigating ? '灌溉进行中' : '暂不需要灌溉',
    risk: needsWater ? '中风险' : '低风险',
    duration: Math.min(20, plot.value.irrigationDuration ?? plot.value.maxDuration ?? 30),
    reasons: [`当前湿度 ${plot.value.humidity}%${needsWater ? `，低于阈值 ${plot.value.threshold}%` : `，高于阈值 ${plot.value.threshold}%`}`, `未来 24 小时降雨概率 ${rain}%`, `设备当前${plot.value.deviceOnline ? '在线' : '离线'}`],
  }
})

function openPlot(plotId) {
  router.push({ path: '/farmer/management', query: { plotId } })
}
function scrollPlots(direction) { plotScroller.value?.scrollBy({ left: direction * 620, behavior: 'smooth' }) }
</script>

<template>
  <div class="farmer-page dashboard-page">
    <div class="dashboard-motto">顺天时，量地利，则用力少而成功多</div>

    <section class="overview-stat-grid">
      <div v-for="item in dashboardStats" :key="item.label" class="overview-stat">
        <span :class="['overview-stat-icon', item.tone]"><el-icon><component :is="Icons[item.icon]" /></el-icon></span>
        <div><label>{{ item.label }}</label><strong>{{ item.value }}<small>{{ item.unit }}</small></strong></div>
      </div>
    </section>

    <OrchardOverview />

    <FarmWheel />

    <section class="content-panel plot-overview">
      <div class="section-head"><div><h3>我的地块</h3><p>共 {{ store.accessiblePlots.length }} 块，仅展示当前账号有权访问的地块</p></div><div class="plot-scroll-actions"><button type="button" aria-label="向左滚动地块" @click="scrollPlots(-1)"><el-icon><ArrowLeft /></el-icon></button><button type="button" aria-label="向右滚动地块" @click="scrollPlots(1)"><el-icon><ArrowRight /></el-icon></button></div></div>
      <div ref="plotScroller" class="plot-card-track"><article v-for="item in store.accessiblePlots" :key="item.plotId" :style="plotBackgroundStyle(item.cropName)" @click="openPlot(item.plotId)"><div class="plot-card-head"><span><strong>{{ item.plotName }}</strong><small>{{ item.cropName }} · {{ item.cropStage }}</small></span><el-icon><ArrowRight /></el-icon></div><div class="mini-metrics"><span>湿度<b>{{ item.humidity }}%</b></span><span>温度<b>{{ item.temperature }}℃</b></span><span>设备<b>{{ item.deviceOnline ? '在线' : '离线' }}</b></span></div></article></div>
    </section>

    <section v-if="plot" class="dashboard-trend">
      <div class="content-panel"><div class="section-head"><div><h3>{{ plot.plotName }} 环境趋势</h3><p>湿度阈值和灌溉事件已叠加显示</p></div><el-button text type="success" @click="router.push('/farmer/management?tab=history')">查看历史</el-button></div><TrendChart :data="trend" /></div>
    </section>

    <section v-if="plot" class="two-column bottom-row">
      <div class="content-panel suggestion"><div class="suggestion-icon"><el-icon><MagicStick /></el-icon></div><div class="suggestion-copy"><div class="suggestion-title"><h3>今日灌溉建议</h3><span class="status-pill warning">{{ recommendation.risk }}</span></div><h2>{{ recommendation.action }}</h2><p>建议时长 {{ recommendation.duration }} 分钟，所有控制操作均需二次确认。</p><div class="evidence-list"><div v-for="reason in recommendation.reasons" :key="reason" class="evidence-item"><el-icon><CircleCheck /></el-icon><span>{{ reason }}</span></div></div></div><el-button type="success" @click="router.push('/farmer/irrigation')">查看并处理</el-button></div>
      <div class="content-panel attention-panel"><div class="section-head attention-head"><div><span class="eyebrow">FIELD NOTICE</span><h3>待处理事项</h3><p>及时关注农田状态，轻松安排今日工作</p></div><el-button class="all-alerts" text @click="router.push('/farmer/alarm')">全部告警 <el-icon><ArrowRight /></el-icon></el-button></div><div v-if="latestAlerts.length" class="alert-list"><button v-for="alert in latestAlerts" :key="alert.alertId" class="alert-item" @click="router.push('/farmer/alarm')"><span class="alert-icon"><el-icon><Warning /></el-icon></span><span class="alert-copy"><span class="alert-title"><strong>{{ alert.plotName }}</strong><i>{{ alert.type }}</i></span><small>{{ alert.reason }}</small><span class="alert-device">{{ alert.deviceId }} · {{ alert.occurTime.slice(0,10) }}</span></span><span class="alert-meta"><strong>{{ alert.value }}</strong><em>{{ alert.occurTime.slice(11,16) }}</em><el-icon><ArrowRight /></el-icon></span></button></div><el-empty v-else :image-size="70" description="田间状态良好，暂无待处理事项" /></div>
    </section>

  </div>
</template>

<style scoped>
.dashboard-motto{margin:2px 0 22px;color:#234b3d;font-size:clamp(21px,2vw,29px);font-weight:700;letter-spacing:.5px}.overview-stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:18px}.overview-stat{min-height:112px;display:flex;align-items:center;justify-content:center;gap:16px;padding:20px;border:1px solid var(--line);border-radius:18px;background:#fff;box-shadow:0 8px 24px rgba(36,86,64,.06)}.overview-stat-icon{width:48px;height:48px;display:grid;place-items:center;flex:0 0 48px;border-radius:50%;font-size:23px}.overview-stat-icon.green{color:#4f942b;background:#edf7e7}.overview-stat-icon.lime{color:#73a932;background:#f0f8e8}.overview-stat-icon.orange{color:#e08a18;background:#fff3df}.overview-stat-icon.blue{color:#2e9bb5;background:#e5f7fa}.overview-stat label{display:block;color:#52675f;font-size:13px;font-weight:600}.overview-stat strong{display:block;margin-top:7px;color:#1f2f29;font-size:27px;line-height:1}.overview-stat small{margin-left:4px;font-size:13px;font-weight:600}.plot-overview{margin-bottom:18px}.plot-scroll-actions{display:flex;gap:8px}.plot-scroll-actions button{width:34px;height:34px;display:grid;place-items:center;border:1px solid var(--line);border-radius:10px;color:#3f6b59;background:#f8fbf9;cursor:pointer}.plot-scroll-actions button:hover{border-color:var(--accent);color:var(--accent);background:#eef7f2}.plot-card-track{display:flex;gap:13px;padding:2px 2px 8px;overflow-x:auto;scroll-behavior:smooth;scroll-snap-type:x proximity;scrollbar-width:thin;scrollbar-color:#b8cec4 transparent}.plot-card-track article{position:relative;min-width:270px;min-height:154px;display:flex;flex:0 0 270px;flex-direction:column;justify-content:space-between;overflow:hidden;padding:17px;border:1px solid rgba(255,255,255,.42);border-radius:15px;background-image:linear-gradient(105deg,rgba(18,55,43,.9),rgba(25,75,57,.57)),var(--plot-bg);background-position:center;background-size:cover;box-shadow:0 8px 20px rgba(28,76,58,.12);color:#fff;cursor:pointer;scroll-snap-align:start;transition:.2s}.plot-card-track article:hover{border-color:rgba(255,255,255,.76);box-shadow:0 13px 28px rgba(25,72,54,.2);transform:translateY(-3px)}.plot-card-head{display:flex;justify-content:space-between}.plot-card-head>.el-icon{color:rgba(255,255,255,.92)}.plot-card-head strong,.plot-card-head small{display:block;text-shadow:0 1px 4px rgba(0,0,0,.28)}.plot-card-head strong{font-size:15px}.plot-card-head small{margin-top:5px;color:rgba(255,255,255,.83);font-size:11px}.mini-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:24px}.mini-metrics span{padding:8px 9px;border:1px solid rgba(255,255,255,.2);border-radius:9px;color:rgba(255,255,255,.78);background:rgba(10,44,33,.32);font-size:10px;backdrop-filter:blur(5px)}.mini-metrics b{display:block;margin-top:3px;color:#fff;font-size:13px;text-shadow:0 1px 3px rgba(0,0,0,.24)}.bottom-row{grid-template-columns:minmax(0,1.4fr) minmax(310px,.8fr)}.suggestion{display:flex;align-items:flex-start;gap:16px;background:linear-gradient(125deg,#f1faf5,#fff)}.suggestion-icon{width:52px;height:52px;display:grid;place-items:center;flex:0 0 52px;border-radius:15px;color:#27835d;background:#dcf2e7;font-size:25px}.suggestion-copy{min-width:0;flex:1}.suggestion-title{display:flex;align-items:center;gap:10px}.suggestion-title h3{margin:0;font-size:14px}.suggestion h2{margin:9px 0 5px;font-size:20px}.suggestion p{margin:0;color:#71807b;font-size:12px}.suggestion>.el-button{align-self:flex-end}.attention-panel{overflow:hidden;background:linear-gradient(145deg,#fff 25%,#f6fbf8);border-color:#dfece5}.attention-head{margin-bottom:14px}.eyebrow{display:block;margin-bottom:5px;color:#74a48e;font-size:9px;font-weight:750;letter-spacing:1.5px}.all-alerts{color:#4d806a}.alert-list{display:grid;gap:9px}.alert-item{width:100%;display:flex;align-items:center;gap:12px;padding:13px;border:1px solid #e8eee9;border-radius:14px;background:rgba(255,255,255,.82);color:inherit;text-align:left;cursor:pointer;transition:border-color .2s,box-shadow .2s,transform .2s}.alert-item:hover{border-color:#b9d7c8;box-shadow:0 8px 20px rgba(52,105,81,.08);transform:translateY(-1px)}.alert-icon{width:38px;height:38px;display:grid;place-items:center;flex:0 0 38px;border-radius:12px;color:#b97742;background:#fff3e8;font-size:17px}.alert-copy{min-width:0;flex:1}.alert-title{display:flex;align-items:center;gap:7px}.alert-title strong{color:#294b3e;font-size:13px}.alert-title i{padding:3px 7px;border-radius:10px;color:#a76338;background:#fff0e3;font-size:9px;font-style:normal;font-weight:650}.alert-copy small{display:block;margin-top:5px;overflow:hidden;color:#75877f;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.alert-device{display:block;margin-top:5px;color:#a0ada7;font-size:9px}.alert-meta{display:grid;grid-template-columns:auto 12px;align-items:center;gap:3px 8px;flex:0 0 auto;text-align:right}.alert-meta strong{grid-row:1;color:#a65f36;font-size:14px}.alert-meta em{grid-row:2;color:#9aa9a2;font-size:10px;font-style:normal}.alert-meta .el-icon{grid-column:2;grid-row:1/3;color:#a9bbb2;font-size:12px}
@media(max-width:1100px){.overview-stat-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:1000px){.bottom-row{grid-template-columns:1fr}}@media(max-width:650px){.overview-stat-grid{grid-template-columns:1fr 1fr;gap:10px}.overview-stat{min-height:92px;padding:14px;justify-content:flex-start}.overview-stat-icon{width:42px;height:42px;flex-basis:42px}.overview-stat strong{font-size:23px}.plot-card-track article{min-width:240px;flex-basis:240px}.suggestion{flex-wrap:wrap}.suggestion>.el-button{margin-left:68px}}@media(max-width:430px){.overview-stat-grid{grid-template-columns:1fr}}
</style>
