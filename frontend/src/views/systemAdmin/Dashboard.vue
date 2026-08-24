<script setup>
import { computed } from 'vue'
import { usePlatformStore } from '@/stores/platform'

const store = usePlatformStore()
const recentAlerts = computed(() => store.alerts.filter((item) => item.status === '未处理').slice(0, 5))
const activeUsers = computed(() => store.users.filter((item) => item.status !== '禁用').length)
const handledAlerts = computed(() => store.alerts.filter((item) => item.status === '已处理').length)
const services = computed(() => [
  { name: '业务数据接口', status: store.loading ? '检查中' : store.loadError ? '异常' : '正常', detail: store.loadError || `已加载 ${store.farms.length} 个农场、${store.plots.length} 个地块` },
  { name: '设备心跳', status: store.offlineDevices ? '需关注' : '正常', detail: `${store.onlineDevices} 台在线，${store.offlineDevices} 台离线或异常` },
  { name: '告警处理', status: store.unhandledAlerts ? '需关注' : '正常', detail: `${store.unhandledAlerts} 项未处理，${handledAlerts.value} 项已处理` },
  { name: '审计与系统配置', status: store.capabilities.auditLogs && store.capabilities.systemSettings ? '正常' : '待接入', detail: '当前数据库未提供审计日志和系统参数表' },
])
</script>

<template>
  <div class="farmer-page admin-page">
    <div class="page-head">
      <div><h1 class="page-title">系统运行概况</h1><p class="page-subtitle">全局农场、设备、用户和告警数据概况。</p></div>
      <div class="page-actions"><span :class="['data-freshness', store.loadError ? 'danger' : '']">{{ store.loading ? '数据加载中' : store.loadError ? '数据加载异常' : '业务数据已同步' }}</span></div>
    </div>
    <section class="farmer-stat-grid">
      <div class="farmer-stat"><div class="stat-symbol"><el-icon><Connection /></el-icon></div><div><label>在线设备</label><strong>{{ store.onlineDevices }}</strong><small>根据启用状态和最近心跳判断</small></div></div>
      <div class="farmer-stat"><div class="stat-symbol red"><el-icon><CircleClose /></el-icon></div><div><label>异常/离线设备</label><strong>{{ store.offlineDevices }}</strong><small>需要排查</small></div></div>
      <div class="farmer-stat"><div class="stat-symbol orange"><el-icon><Warning /></el-icon></div><div><label>未处理告警</label><strong>{{ store.unhandledAlerts }}</strong><small>全系统</small></div></div>
      <div class="farmer-stat"><div class="stat-symbol blue"><el-icon><User /></el-icon></div><div><label>启用用户</label><strong>{{ activeUsers }}</strong><small>账号 active 状态</small></div></div>
    </section>
    <section class="two-column">
      <div class="content-panel">
        <div class="section-head"><div><h3>业务数据规模</h3><p>全部数值来自当前数据库查询结果</p></div><el-tag :type="store.loadError ? 'danger' : 'success'" effect="plain">{{ store.loadError ? '异常' : '已同步' }}</el-tag></div>
        <div class="receive-grid">
          <article><span>农场</span><strong>{{ store.farms.length }}</strong><small>启用与停用农场</small></article>
          <article><span>地块</span><strong>{{ store.plots.length }}</strong><small>按 farm_id 关联农场</small></article>
          <article><span>设备</span><strong>{{ store.devices.length }}</strong><small>按 plot_id 关联地块</small></article>
          <article><span>告警</span><strong>{{ store.alerts.length }}</strong><small>包含全部处理状态</small></article>
        </div>
      </div>
      <div class="content-panel">
        <div class="section-head"><div><h3>服务与数据能力</h3><p>只展示当前能够核验的状态</p></div></div>
        <div class="service-list"><div v-for="item in services" :key="item.name"><span :class="['service-dot', { warning: item.status !== '正常' }]"/><p><strong>{{ item.name }}</strong><small>{{ item.detail }}</small></p><em>{{ item.status }}</em></div></div>
      </div>
    </section>
    <section class="two-column">
      <div class="content-panel">
        <div class="section-head"><div><h3>最新未处理告警</h3><p>跨农场异常汇总</p></div><router-link to="/admin/alerts">查看全部</router-link></div>
        <div v-for="item in recentAlerts" :key="item.id" class="admin-alert"><span class="status-pill danger">{{ item.type }}</span><p><strong>{{ item.farmName }} · {{ item.plotName }}</strong><small>{{ item.occurTime }} · {{ item.deviceId || '无关联设备' }}</small></p><em>{{ item.value }}</em></div>
        <el-empty v-if="!recentAlerts.length" description="暂无未处理告警" :image-size="60" />
      </div>
      <div class="content-panel">
        <div class="section-head"><div><h3>数据关联链路</h3><p>当前页面使用的数据库关系</p></div></div>
        <div class="chain"><span>用户授权<i/></span><span>农场<i/></span><span>地块<i/></span><span>设备<i/></span><span>上报/灌溉<i/></span><span>告警</span></div>
        <div class="chain-note"><el-icon><CircleCheckFilled /></el-icon> 页面数据按授权范围和外键关系联动，设备在线状态由 active 与 last_heartbeat 计算</div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.receive-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.receive-grid article{padding:15px;border-radius:12px;background:#f6f8fb}.receive-grid span,.receive-grid strong,.receive-grid small{display:block}.receive-grid span{color:#7e8797;font-size:11px}.receive-grid strong{margin:5px 0;color:#383e55;font-size:22px}.receive-grid small{color:#969cab;font-size:10px}.service-list{display:grid}.service-list>div{display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #eff0f5}.service-list>div:last-child{border:0}.service-dot{width:8px;height:8px;border-radius:50%;background:#43a678;box-shadow:0 0 0 4px #e8f5ef}.service-dot.warning{background:#e6a23c;box-shadow:0 0 0 4px #fff1d8}.service-list p{flex:1;margin:0}.service-list strong,.service-list small{display:block}.service-list strong{font-size:13px}.service-list small{margin-top:4px;color:#949aaa;font-size:10px}.service-list em{color:#3b906a;font-size:11px;font-style:normal}.admin-alert{display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #eff0f5}.admin-alert p{min-width:0;flex:1;margin:0}.admin-alert strong,.admin-alert small{display:block}.admin-alert strong{font-size:12px}.admin-alert small{margin-top:4px;color:#9299a8;font-size:10px}.admin-alert em{color:#c34f5b;font-size:12px;font-style:normal}.section-head a{color:#6b5bb5;font-size:12px;text-decoration:none}.chain{display:flex;align-items:center;justify-content:center;gap:4px;padding:28px 5px}.chain span{display:flex;align-items:center;color:#50576b;font-size:11px;white-space:nowrap}.chain i{width:18px;height:2px;margin-left:4px;background:#94d1b2}.chain-note{padding:10px;border-radius:10px;color:#377e60;background:#eef8f3;font-size:11px;text-align:center}.chain-note .el-icon{vertical-align:-2px}.data-freshness.danger{color:#c34f5b}@media(max-width:600px){.receive-grid{grid-template-columns:1fr}.chain{overflow-x:auto;justify-content:flex-start}}
</style>
