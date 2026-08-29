<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useFarmerStore } from '@/stores/farmer'
import * as Icons from '@element-plus/icons-vue'
import TrendChart from '@/components/TrendChart.vue'
import { orangeCropBackgrounds, orangeCropFallbacks } from '@/utils/cropAssets'
import FarmWheel from '@/components/FarmWheel.vue'

const router = useRouter()
const store = useFarmerStore()
const plotScroller = ref(null)
const cropBackgrounds = orangeCropBackgrounds
const plotBackgroundStyle = (cropName) => ({
  '--plot-bg': `url(${cropBackgrounds[cropName] || orangeCropFallbacks[0]})`,
})
const plot = computed(() => store.currentPlot)
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
  const needsWater = plot.value.humidity < plot.value.threshold
  return {
    action: needsWater ? '建议短时灌溉' : plot.value.irrigating ? '灌溉进行中' : '暂不需要灌溉',
    risk: needsWater ? '中风险' : '低风险',
    duration: Math.min(20, plot.value.irrigationDuration ?? plot.value.maxDuration ?? 30),
    reasons: [`当前湿度 ${plot.value.humidity}%${needsWater ? `，低于阈值 ${plot.value.threshold}%` : `，高于阈值 ${plot.value.threshold}%`}`, '当前建议仅依据农田监测数据，未使用实时天气', `设备当前${plot.value.deviceOnline ? '在线' : '离线'}`],
  }
})

function openPlot(plotId) {
  router.push({ path: '/farmer/management', query: { plotId } })
}
function scrollPlots(direction) { plotScroller.value?.scrollBy({ left: direction * 620, behavior: 'smooth' }) }
</script>

<template>
  <div class="farmer-page dashboard-page">
    <div class="dashboard-motto">
      <span class="motto-copy">顺天时，量地利，则用力少而成功多</span>
      <svg class="motto-sprig" viewBox="0 0 150 54" aria-hidden="true">
        <path class="sprig-stem" d="M3 45 C35 40, 60 27, 88 13 C106 5, 126 7, 146 2" />
        <path class="sprig-stem light" d="M52 31 C76 37, 104 34, 132 24" />
        <path class="sprig-leaf green" d="M29 38 C20 25, 23 17, 28 12 C36 21, 36 30, 29 38Z" />
        <path class="sprig-leaf green soft" d="M43 33 C39 21, 44 14, 51 10 C56 21, 52 29, 43 33Z" />
        <path class="sprig-leaf gold" d="M67 26 C63 17, 67 11, 75 7 C78 16, 75 23, 67 26Z" />
        <path class="sprig-leaf gold soft" d="M82 20 C81 12, 87 7, 95 5 C95 13, 91 18, 82 20Z" />
        <path class="sprig-leaf gold" d="M96 32 C101 23, 109 21, 117 23 C112 31, 105 34, 96 32Z" />
        <path class="sprig-leaf gold soft" d="M118 25 C124 18, 132 17, 140 20 C134 27, 126 29, 118 25Z" />
      </svg>
    </div>

    <section class="overview-stat-grid">
      <div v-for="item in dashboardStats" :key="item.label" class="overview-stat">
        <span :class="['overview-stat-icon', item.tone]"><el-icon><component :is="Icons[item.icon]" /></el-icon></span>
        <div><label>{{ item.label }}</label><strong>{{ item.value }}<small>{{ item.unit }}</small></strong></div>
      </div>
    </section>

    <FarmWheel v-if="store.accessiblePlots.length" :plots="store.accessiblePlots" />
  </div>
</template>

<style scoped>
.dashboard-motto{position:relative;width:max-content;max-width:100%;display:flex;align-items:center;isolation:isolate;margin:2px 0 22px;padding:3px 10px 7px 0}.dashboard-motto::before{position:absolute;z-index:-1;top:48%;left:58%;width:86px;height:42px;content:'';border-radius:50%;background:radial-gradient(ellipse,rgba(238,190,89,.18),rgba(238,190,89,0) 70%);transform:translate(-50%,-50%)}.dashboard-motto::after{position:absolute;z-index:-1;right:88px;bottom:2px;width:44%;height:7px;content:'';border-radius:50%;background:linear-gradient(90deg,transparent,rgba(115,166,104,.16),rgba(225,184,82,.12),transparent);filter:blur(2px)}.motto-copy{color:#155b3d;font-family:"STKaiti","KaiTi","FangSong","Noto Serif SC",serif;font-size:clamp(24px,2.35vw,35px);font-weight:700;line-height:1.35;letter-spacing:1.5px;text-shadow:0 1px 0 rgba(255,255,255,.9),0 3px 10px rgba(36,96,65,.08)}.motto-sprig{width:132px;height:48px;flex:0 0 132px;margin-left:7px;overflow:visible;transform:rotate(-4deg);transform-origin:left center}.sprig-stem{fill:none;stroke:#d8b457;stroke-linecap:round;stroke-width:1.6}.sprig-stem.light{stroke:#e7cc86;stroke-width:1}.sprig-leaf{stroke-linejoin:round;stroke-width:.6}.sprig-leaf.green{fill:#8cbf78;stroke:#75a962}.sprig-leaf.gold{fill:#e4c56e;stroke:#d1ac4f}.sprig-leaf.soft{opacity:.58}.overview-stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:18px}.overview-stat{min-height:112px;display:flex;align-items:center;justify-content:center;gap:16px;padding:20px;border:1px solid var(--line);border-radius:18px;background:#fff;box-shadow:0 8px 24px rgba(36,86,64,.06)}.overview-stat-icon{width:48px;height:48px;display:grid;place-items:center;flex:0 0 48px;border-radius:50%;font-size:23px}.overview-stat-icon.green{color:#4f942b;background:#edf7e7}.overview-stat-icon.lime{color:#73a932;background:#f0f8e8}.overview-stat-icon.orange{color:#e08a18;background:#fff3df}.overview-stat-icon.blue{color:#2e9bb5;background:#e5f7fa}.overview-stat label{display:block;color:#52675f;font-size:13px;font-weight:600}.overview-stat strong{display:block;margin-top:7px;color:#1f2f29;font-size:27px;line-height:1}.overview-stat small{margin-left:4px;font-size:13px;font-weight:600}.plot-overview{margin-bottom:18px}.plot-scroll-actions{display:flex;gap:8px}.plot-scroll-actions button{width:34px;height:34px;display:grid;place-items:center;border:1px solid var(--line);border-radius:10px;color:#3f6b59;background:#f8fbf9;cursor:pointer}.plot-scroll-actions button:hover{border-color:var(--accent);color:var(--accent);background:#eef7f2}.plot-card-track{display:flex;gap:13px;padding:2px 2px 8px;overflow-x:auto;scroll-behavior:smooth;scroll-snap-type:x proximity;scrollbar-width:thin;scrollbar-color:#b8cec4 transparent}.plot-card-track article{position:relative;min-width:270px;min-height:154px;display:flex;flex:0 0 270px;flex-direction:column;justify-content:space-between;overflow:hidden;padding:17px;border:1px solid rgba(255,255,255,.42);border-radius:15px;background-image:linear-gradient(105deg,rgba(18,55,43,.9),rgba(25,75,57,.57)),var(--plot-bg);background-position:center;background-size:cover;box-shadow:0 8px 20px rgba(28,76,58,.12);color:#fff;cursor:pointer;scroll-snap-align:start;transition:.2s}.plot-card-track article:hover{border-color:rgba(255,255,255,.76);box-shadow:0 13px 28px rgba(25,72,54,.2);transform:translateY(-3px)}.plot-card-head{display:flex;justify-content:space-between}.plot-card-head>.el-icon{color:rgba(255,255,255,.92)}.plot-card-head strong,.plot-card-head small{display:block;text-shadow:0 1px 4px rgba(0,0,0,.28)}.plot-card-head strong{font-size:15px}.plot-card-head small{margin-top:5px;color:rgba(255,255,255,.83);font-size:11px}.mini-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:24px}.mini-metrics span{padding:8px 9px;border:1px solid rgba(255,255,255,.2);border-radius:9px;color:rgba(255,255,255,.78);background:rgba(10,44,33,.32);font-size:10px;backdrop-filter:blur(5px)}.mini-metrics b{display:block;margin-top:3px;color:#fff;font-size:13px;text-shadow:0 1px 3px rgba(0,0,0,.24)}.bottom-row{grid-template-columns:minmax(0,1.4fr) minmax(310px,.8fr)}.suggestion{display:flex;align-items:flex-start;gap:16px;background:linear-gradient(125deg,#f1faf5,#fff)}.suggestion-icon{width:52px;height:52px;display:grid;place-items:center;flex:0 0 52px;border-radius:15px;color:#27835d;background:#dcf2e7;font-size:25px}.suggestion-copy{min-width:0;flex:1}.suggestion-title{display:flex;align-items:center;gap:10px}.suggestion-title h3{margin:0;font-size:14px}.suggestion h2{margin:9px 0 5px;font-size:20px}.suggestion p{margin:0;color:#71807b;font-size:12px}.suggestion>.el-button{align-self:flex-end}.attention-panel{overflow:hidden;background:linear-gradient(145deg,#fff 25%,#f6fbf8);border-color:#dfece5}.attention-head{margin-bottom:14px}.eyebrow{display:block;margin-bottom:5px;color:#74a48e;font-size:9px;font-weight:750;letter-spacing:1.5px}.all-alerts{color:#4d806a}.alert-list{display:grid;gap:9px}.alert-item{width:100%;display:flex;align-items:center;gap:12px;padding:13px;border:1px solid #e8eee9;border-radius:14px;background:rgba(255,255,255,.82);color:inherit;text-align:left;cursor:pointer;transition:border-color .2s,box-shadow .2s,transform .2s}.alert-item:hover{border-color:#b9d7c8;box-shadow:0 8px 20px rgba(52,105,81,.08);transform:translateY(-1px)}.alert-icon{width:38px;height:38px;display:grid;place-items:center;flex:0 0 38px;border-radius:12px;color:#b97742;background:#fff3e8;font-size:17px}.alert-copy{min-width:0;flex:1}.alert-title{display:flex;align-items:center;gap:7px}.alert-title strong{color:#294b3e;font-size:13px}.alert-title i{padding:3px 7px;border-radius:10px;color:#a76338;background:#fff0e3;font-size:9px;font-style:normal;font-weight:650}.alert-copy small{display:block;margin-top:5px;overflow:hidden;color:#75877f;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.alert-device{display:block;margin-top:5px;color:#a0ada7;font-size:9px}.alert-meta{display:grid;grid-template-columns:auto 12px;align-items:center;gap:3px 8px;flex:0 0 auto;text-align:right}.alert-meta strong{grid-row:1;color:#a65f36;font-size:14px}.alert-meta em{grid-row:2;color:#9aa9a2;font-size:10px;font-style:normal}.alert-meta .el-icon{grid-column:2;grid-row:1/3;color:#a9bbb2;font-size:12px}
@media(max-width:1100px){.overview-stat-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:1000px){.bottom-row{grid-template-columns:1fr}}@media(max-width:650px){.overview-stat-grid{grid-template-columns:1fr 1fr;gap:10px}.overview-stat{min-height:92px;padding:14px;justify-content:flex-start}.overview-stat-icon{width:42px;height:42px;flex-basis:42px}.overview-stat strong{font-size:23px}.plot-card-track article{min-width:240px;flex-basis:240px}.suggestion{flex-wrap:wrap}.suggestion>.el-button{margin-left:68px}}@media(max-width:430px){.overview-stat-grid{grid-template-columns:1fr}}
@media(max-width:650px){.dashboard-motto{align-items:flex-end;margin-bottom:18px}.motto-copy{font-size:clamp(22px,6vw,28px);letter-spacing:.5px}.motto-sprig{width:86px;height:38px;flex-basis:86px;margin-left:2px}}@media(max-width:430px){.motto-sprig{display:none}.dashboard-motto::after{right:0;width:62%}}
</style>

<style scoped>
.motto-copy{color:#8b451b;text-shadow:0 1px 0 rgba(255,255,255,.9),0 3px 10px rgba(139,69,27,.1)}
.overview-stat{background:#fffdfa;box-shadow:0 8px 24px rgba(112,58,23,.07)}
.overview-stat-icon.green,.overview-stat-icon.lime{color:#d56c1b;background:#fff0df}
.suggestion{background:linear-gradient(125deg,#fff5e9,#fffdfa)}.suggestion-icon{color:#cb6318;background:#ffe8cf}
.overview-stat label{color:#786457}.overview-stat strong{color:#482b19}
.plot-card-track article{background-image:linear-gradient(105deg,rgba(70,34,14,.9),rgba(117,58,18,.5)),var(--plot-bg);box-shadow:0 8px 20px rgba(102,50,17,.15)}
.mini-metrics span{background:rgba(62,28,9,.36)}
.attention-panel{border-color:#efdfd1;background:linear-gradient(145deg,#fffdfa 25%,#fff5ea)}
.eyebrow,.all-alerts{color:#b3622d}.alert-title strong{color:#59351f}
</style>
