<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Cloudy, Drizzling, Lightning, PartlyCloudy, Pouring, Sunny } from '@element-plus/icons-vue'
import { useFarmerStore } from '@/stores/farmer'
import { useUserStore } from '@/stores/user'
import { listTasks } from '@/api/task'
import { parseDate } from '@/utils/dataAdapters'
import FarmerDashboardIcon from '@/components/FarmerDashboardIcon.vue'

const router = useRouter()
const farmerStore = useFarmerStore()
const userStore = useUserStore()
const loading = ref(true)
const todayTasks = ref([])
const upcomingTasks = ref([])
const overdueTasks = ref([])

const farmPlotIds = computed(() => new Set(farmerStore.farmPlots.map((plot) => plot.plotId)))
const farmTasks = computed(() => todayTasks.value.filter((task) => farmPlotIds.value.has(task.plotId)))
const farmUpcomingTasks = computed(() => upcomingTasks.value.filter((task) => farmPlotIds.value.has(task.plotId)))
const actionableTasks = computed(() => farmTasks.value.filter((task) => !['completed', 'cancelled'].includes(task.status)).slice(0, 3))
const completedTasks = computed(() => farmTasks.value.filter((task) => task.status === 'completed'))
const farmOverdueTasks = computed(() => overdueTasks.value.filter((task) => farmPlotIds.value.has(task.plotId)))
const allActionableAlerts = computed(() => {
  const uniqueAlerts = new Map()
  farmerStore.farmAlerts
    .filter((alert) => ['未处理', '处理中'].includes(alert.status))
    .forEach((alert) => {
      const key = `${alert.plotId}:${alert.type}`
      if (!uniqueAlerts.has(key)) uniqueAlerts.set(key, alert)
    })
  return [...uniqueAlerts.values()]
})
const actionableAlerts = computed(() => allActionableAlerts.value.slice(0, 2))
const actionableAlertCount = computed(() => allActionableAlerts.value.length)
const greeting = computed(() => {
  const hour = new Date().getHours()
  return hour < 11 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
})
const greetingWeatherIcon = computed(() => {
  const condition = String(farmerStore.weather?.condition || '')
  if (condition.includes('雷')) return Lightning
  if (/大雨|暴雨/.test(condition)) return Pouring
  if (/雨|毛毛雨/.test(condition)) return Drizzling
  if (condition.includes('多云')) return PartlyCloudy
  if (/阴|雾|雪/.test(condition)) return Cloudy
  return Sunny
})
const greetingWeatherTitle = computed(() => {
  const weather = farmerStore.weather
  if (!weather?.condition) return '暂无天气数据'
  const temperature = Number(weather.temperature)
  return Number.isFinite(temperature) ? `${weather.condition} ${temperature}℃` : weather.condition
})
const sevenDayPlan = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return Array.from({ length: 7 }, (_, offset) => {
    const date = new Date(today)
    date.setDate(today.getDate() + offset)
    const key = formatDateKey(date)
    const tasks = farmUpcomingTasks.value.filter((task) => String(task.scheduledDate || '').slice(0, 10) === key)
    return { key, date, tasks, today: offset === 0 }
  })
})
const futureTaskCount = computed(() => sevenDayPlan.value.reduce((count, day) => count + day.tasks.length, 0))

function formatDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
function dayLabel(day) {
  if (day.today) return '今天'
  return `${day.date.getMonth() + 1}/${day.date.getDate()}`
}
function weekLabel(day) {
  if (day.today) return `${day.date.getMonth() + 1}/${day.date.getDate()}`
  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][day.date.getDay()]
}
function taskSourceLabel(task) { return task.source === 'ad_hoc' ? '计划外农事' : '计划任务' }
function taskTitle(task) {
  const title = String(task.title || '').trim()
  return title && !/^\?+$/.test(title) ? title : '待执行农事'
}
function taskDue(task) { return task.status === 'overdue' ? '已逾期' : task.status === 'completed' ? '已完成' : '今天' }
function taskTone(task) { return task.status === 'overdue' ? 'danger' : task.status === 'completed' ? 'completed' : 'normal' }
function alertKind(alert) {
  const value = `${alert.typeCode || ''} ${alert.type || ''}`.toLowerCase()
  if (value.includes('device_offline') || value.includes('设备离线')) return 'offline'
  if (value.includes('moisture') || value.includes('humidity') || value.includes('湿度') || value.includes('墒情')) return 'moisture'
  return 'other'
}
function alertTone(alert) {
  if (alertKind(alert) === 'offline') return 'critical'
  if (alertKind(alert) === 'moisture') return 'attention'
  return alert.level === '高' ? 'critical' : 'attention'
}
function alertTitle(alert) {
  let type = String(alert.type || '告警').replaceAll('土壤墒情', '土壤湿度').replaceAll('墒情', '土壤湿度')
  if (type === '湿度过低') type = '土壤湿度偏低'
  if (type === '湿度偏高') type = '土壤湿度偏高'
  return `${alert.plotName} · ${type}`
}
function alertDescription(alert) {
  const kind = alertKind(alert)
  if (kind === 'offline') return '设备连接已中断，可能影响今日灌溉任务'
  if (kind === 'moisture') {
    const type = `${alert.typeCode || ''} ${alert.type || ''}`.toLowerCase()
    const direction = type.includes('high') || type.includes('偏高') ? '高于' : '低于'
    const value = alert.value !== undefined && alert.value !== null && alert.value !== '-' ? ` ${alert.value}%` : ''
    const threshold = alert.threshold !== undefined && alert.threshold !== null && alert.threshold !== '-' ? ` ${alert.threshold}%` : '设定范围'
    return `当前土壤湿度${value}，${direction}${threshold}，可能影响作物正常生长`
  }
  return `${alert.reason || '告警状态异常'}，可能影响田间作业安排`
}
function alertTime(alert) {
  const date = parseDate(alert.occurTime)
  if (!date) return '-'
  const now = new Date()
  const today = formatDateKey(now)
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  const time = new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(date)
  const dateKey = formatDateKey(date)
  if (dateKey === today) return `今天 ${time}`
  if (dateKey === formatDateKey(yesterday)) return `昨天 ${time}`
  return `${date.getMonth() + 1}月${date.getDate()}日 ${time}`
}
function openTasks() { router.push('/farmer/tasks') }
function openAlerts() { router.push('/farmer/alarm') }

async function loadDashboard() {
  loading.value = true
  try {
    const [today, next7days, overdue] = await Promise.all([
      listTasks({ scope: 'today' }),
      listTasks({ scope: 'next7days' }),
      listTasks({ scope: 'overdue' }),
    ])
    todayTasks.value = today
    upcomingTasks.value = next7days
    overdueTasks.value = overdue
  } catch {
    todayTasks.value = []
    upcomingTasks.value = []
    overdueTasks.value = []
  } finally {
    loading.value = false
  }
}

watch(() => farmerStore.selectedFarmId, loadDashboard, { immediate: true })
</script>

<template>
  <div class="farmer-page farmer-dashboard">
    <section class="dashboard-welcome">
      <div>
        <h1>{{ greeting }}，{{ userStore.user?.displayName || '李四' }}<span class="greeting-weather" :title="greetingWeatherTitle"><el-icon><component :is="greetingWeatherIcon" /></el-icon></span></h1>
        <p>专注田间管理，收获每一份丰收</p>
      </div>
      <section class="overview-strip">
        <article class="overview-item"><span class="overview-icon"><FarmerDashboardIcon name="tasks" /></span><div><small>待办任务</small><strong>{{ actionableTasks.length }} <em>项</em></strong><p>今日需要完成</p></div></article>
        <article class="overview-item warning"><span class="overview-icon"><FarmerDashboardIcon name="warning" /></span><div><small>需要处理</small><strong>{{ actionableAlertCount }} <em>条</em></strong><p>待处理告警</p></div></article>
        <article class="overview-item"><span class="overview-icon"><el-icon><Calendar /></el-icon></span><div><small>未来 7 天计划</small><strong>{{ futureTaskCount }} <em>项</em></strong><p>即将到来的农事</p></div></article>
      </section>
    </section>

    <section class="dashboard-columns">
      <article class="dashboard-panel task-card">
        <header class="panel-title"><div><h2><FarmerDashboardIcon name="tasks" />今日待办</h2><p>今天还有 {{ actionableTasks.length }} 项任务需要完成</p></div><button @click="openTasks">查看全部 <el-icon><ArrowRight /></el-icon></button></header>
        <el-skeleton v-if="loading" :rows="3" animated />
        <div v-else-if="farmTasks.length" class="dashboard-task-list">
          <button v-for="task in farmTasks.slice(0, 3)" :key="task.id" class="dashboard-task" @click="openTasks">
            <span :class="['task-check', taskTone(task)]"><el-icon v-if="task.status === 'completed'"><Check /></el-icon></span>
            <span class="task-copy">
              <b>{{ taskTitle(task) }}</b>
              <small><span class="task-plot">{{ task.plotName }}</span><span class="task-source-tag">{{ taskSourceLabel(task) }}</span></small>
            </span>
            <span :class="['due-label', taskTone(task)]">{{ taskDue(task) }}</span><el-icon class="task-arrow"><ArrowRight /></el-icon>
          </button>
        </div>
        <el-empty v-else :image-size="52" description="今天没有待办农事" />
        <footer class="task-footer"><span>待完成 <b>{{ actionableTasks.length }}</b></span><span>已完成 <b>{{ completedTasks.length }}</b></span><span>逾期 <b class="orange">{{ farmOverdueTasks.length }}</b></span></footer>
      </article>

      <article class="dashboard-panel alert-card">
        <header class="panel-title"><div><h2 class="warning-title"><FarmerDashboardIcon name="warning" />需要处理</h2><p>有 {{ actionableAlertCount }} 条告警需要你处理</p></div><button @click="openAlerts">查看全部（{{ actionableAlertCount }}）<el-icon><ArrowRight /></el-icon></button></header>
        <div v-if="actionableAlerts.length" class="dashboard-alert-list">
          <article v-for="alert in actionableAlerts" :key="alert.alertId" :class="['dashboard-alert', alertTone(alert)]"><span class="alert-dot"></span><div><b>{{ alertTitle(alert) }}</b><p>{{ alertDescription(alert) }}</p><small>发现时间：{{ alertTime(alert) }}</small></div><button @click="openAlerts">去处理</button></article>
        </div>
        <el-empty v-else :image-size="72" description="暂无需要处理的告警" />
      </article>
    </section>

    <section class="dashboard-panel schedule-card">
      <header class="panel-title"><div><h2><el-icon><Calendar /></el-icon>近期安排 <span>（未来 7 天）</span></h2></div><button @click="openTasks">查看完整计划 <el-icon><ArrowRight /></el-icon></button></header>
      <div class="schedule-grid"><article v-for="day in sevenDayPlan" :key="day.key" :class="['schedule-day', { active: day.today }]"><h3>{{ dayLabel(day) }} <small>{{ weekLabel(day) }}</small></h3><b class="schedule-count">{{ day.tasks.length }} 项</b><ul v-if="day.tasks.length"><li v-for="task in day.tasks.slice(0, 2)" :key="task.id">{{ taskTitle(task) }}</li></ul><p v-else>暂无计划</p></article></div>
    </section>
  </div>
</template>

<style scoped>
.farmer-dashboard{padding:5px 0}.dashboard-welcome{display:grid;grid-template-columns:minmax(350px,.78fr) minmax(620px,1.22fr);align-items:center;gap:28px;margin:5px 14px 18px}.dashboard-welcome h1{display:flex;align-items:center;flex-wrap:wrap;margin:0;color:#245541;font-size:40px!important;font-weight:800;line-height:1.25}.greeting-weather{display:inline-grid;width:42px;height:42px;place-items:center;flex:0 0 42px;margin-left:12px;color:#efa70e;font-size:38px;font-weight:400}.greeting-weather .el-icon{width:1em;height:1em}.dashboard-welcome>div>p{margin:12px 0 0;color:#687770;font-size:17px}.overview-strip{display:grid;grid-template-columns:repeat(3,1fr);padding:27px 22px;border:1px solid #edf0eb;border-radius:14px;background:#fff;box-shadow:0 9px 25px rgba(31,77,54,.07)}.overview-item{display:flex;align-items:center;gap:15px;min-width:0;padding:0 20px;border-right:1px solid #e4e9e4}.overview-item:first-child{padding-left:0}.overview-item:last-child{padding-right:0;border-right:0}.overview-icon{display:grid;width:50px;height:50px;place-items:center;flex:0 0 50px;border-radius:12px;color:#487627;background:#f3f7e9;font-size:28px}.overview-item.warning .overview-icon{color:#eca912;background:#fff8e8}.overview-item small,.overview-item strong,.overview-item p{display:block}.overview-item small{color:#26352e;font-size:15px;font-weight:650}.overview-item strong{margin-top:6px;color:#397320;font-size:30px;line-height:1}.overview-item strong em{font-size:17px;font-style:normal}.overview-item p{margin:8px 0 0;color:#77827d;font-size:13px}.dashboard-columns{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-bottom:18px}.dashboard-panel{border:1px solid #edf0eb;border-radius:14px;background:#fff;box-shadow:0 8px 25px rgba(31,77,54,.055)}.task-card,.alert-card{min-height:400px;padding:23px 24px}.panel-title{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.panel-title h2{display:flex;align-items:center;gap:12px;margin:0;color:#1d2a23;font-size:19px}.panel-title h2 .el-icon{color:#467d27;font-size:26px}.panel-title h2>.farmer-dashboard-icon{flex:0 0 26px;width:26px;height:26px;color:#467d27}.panel-title h2 span{font-size:14px;font-weight:500}.panel-title p{margin:8px 0 0;color:#7a8580;font-size:14px}.panel-title button{display:inline-flex;align-items:center;gap:4px;padding:4px;border:0;color:#2e762f;background:transparent;font:inherit;font-size:14px;font-weight:600;cursor:pointer}.warning-title .el-icon{color:#eead0a!important}.panel-title .warning-title>.farmer-dashboard-icon{color:#eead0a}.dashboard-task-list{margin-top:20px;border-top:1px solid #e7ebe7}.dashboard-task{display:grid;grid-template-columns:36px minmax(0,1fr) auto 16px;align-items:center;gap:14px;width:100%;min-height:92px;padding:13px 4px;border:0;border-bottom:1px solid #e7ebe7;color:inherit;background:#fff;text-align:left;cursor:pointer}.dashboard-task:hover b{color:#297846}.task-check{display:grid;width:27px;height:27px;place-items:center;border:2px solid #c2c9c4;border-radius:5px;color:#fff}.task-check.completed{border-color:#477a22;background:#477a22}.task-copy b,.task-copy small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.task-copy b{color:#202b25;font-size:16px}.task-copy small{margin-top:7px;color:#78827e;font-size:13px}.due-label{color:#ed4b38;font-size:14px;font-weight:650}.due-label.completed{color:#6e7a74}.due-label.danger{color:#e13f33}.task-arrow{color:#78827e}.task-footer{display:grid;grid-template-columns:repeat(3,1fr);margin-top:4px;padding:17px 0 0}.task-footer span{padding:0 18px;border-right:1px solid #e5eae6;color:#243027;text-align:center;font-size:14px}.task-footer span:first-child{padding-left:0}.task-footer span:last-child{padding-right:0;border:0}.task-footer b{margin-left:8px;color:#3b7726;font-size:17px}.task-footer b.orange{color:#eb9a00}.dashboard-alert-list{display:grid;gap:14px;margin-top:22px}.dashboard-alert{display:grid;grid-template-columns:18px minmax(0,1fr) auto;align-items:center;gap:16px;padding:23px 22px;border-radius:12px}.dashboard-alert.critical{background:#fff6f2}.dashboard-alert.attention{background:#fffaf0}.alert-dot{width:18px;height:18px;border-radius:50%;background:#ef5737}.attention .alert-dot{background:#f0ac15}.dashboard-alert b{color:#1d2621;font-size:16px}.dashboard-alert p{margin:9px 0;color:#4e5b54;font-size:14px}.dashboard-alert small{color:#76817d;font-size:13px}.dashboard-alert button{padding:11px 20px;border:1px solid #ef5b43;border-radius:7px;color:#e44931;background:#fff;font:inherit;font-size:14px;font-weight:650;cursor:pointer}.attention button{border-color:#eca813;color:#d59105}.schedule-card{padding:22px 24px}.schedule-grid{display:grid;grid-template-columns:repeat(7,minmax(110px,1fr));gap:13px;margin-top:20px}.schedule-day{min-height:163px;padding:17px 15px;border-radius:10px;background:#fbfcfb}.schedule-day.active{border:1px solid #c8df9c;background:#f8fcf0}.schedule-day h3{margin:0;color:#151d18;font-size:16px}.schedule-day h3 small{margin-left:4px;font-size:13px;font-weight:500}.schedule-count{display:inline-block;margin:12px 0 10px;padding:3px 11px;border-radius:12px;background:#f2f4f2;color:#202a24;font-size:13px}.schedule-day ul{margin:0;padding-left:16px;color:#202a24;font-size:13px;line-height:2}.schedule-day p{margin:13px 0 0;color:#7e8783;font-size:13px;text-align:center}@media(max-width:1180px){.dashboard-welcome{grid-template-columns:1fr}.dashboard-columns{grid-template-columns:1fr}.schedule-grid{grid-template-columns:repeat(4,1fr)}}@media(max-width:720px){.dashboard-welcome{margin:0 0 16px}.dashboard-welcome h1{font-size:30px!important}.greeting-weather{width:34px;height:34px;flex-basis:34px;font-size:31px}.overview-strip{grid-template-columns:1fr;padding:8px 18px}.overview-item,.overview-item:first-child,.overview-item:last-child{padding:14px 0;border-right:0;border-bottom:1px solid #e4e9e4}.overview-item:last-child{border-bottom:0}.task-card,.alert-card,.schedule-card{padding:18px}.dashboard-task{grid-template-columns:32px minmax(0,1fr) auto}.task-arrow{display:none}.dashboard-alert{grid-template-columns:14px minmax(0,1fr);padding:17px}.dashboard-alert button{grid-column:2;justify-self:start}.schedule-grid{grid-template-columns:repeat(2,1fr)}}
.task-card{display:flex;flex-direction:column}.dashboard-task-list{flex:1}.task-card>.el-empty,.task-card>.el-skeleton{flex:1}.task-copy{min-width:0}.task-copy small{display:flex;align-items:center;gap:10px;overflow:visible}.task-plot{min-width:0;overflow:hidden;text-overflow:ellipsis}.task-source-tag{flex:0 0 auto;padding:3px 9px;border-radius:5px;color:#3f7628;background:#eef7df;font-size:12px;line-height:1.2}.task-footer{margin-top:auto}
</style>
