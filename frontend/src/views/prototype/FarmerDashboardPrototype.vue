<script setup>
import {
  ArrowRight,
  Bell,
  Calendar,
  DataAnalysis,
  Drizzling,
  Fold,
  Grid,
  House,
  List,
  Tools,
  Warning,
  WarningFilled,
} from '@element-plus/icons-vue'

const navigation = [
  { label: '农场首页', icon: House, active: true },
  { label: '地块管理', icon: DataAnalysis },
  { label: '我的农事', icon: List },
  { label: '智慧灌溉', icon: Drizzling },
  { label: '告警中心', icon: Warning },
]

const irrigationActions = [
  { plot: '一号田地', moisture: '40.87%', threshold: '下限 55%' },
  { plot: '二号田地', moisture: '40.54%', threshold: '下限 55%' },
]
</script>

<template>
  <div class="prototype-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">禾</span>
        <span class="brand-copy"><strong>智慧农业平台</strong><small>SMART AGRICULTURE</small></span>
      </div>

      <nav class="nav" aria-label="农户功能导航">
        <button v-for="item in navigation" :key="item.label" :class="['nav-item', { active: item.active }]">
          <component :is="item.icon" :size="20" stroke-width="2" />
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <button class="collapse"><Fold /><span>收起菜单</span></button>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div class="topbar-actions">
          <time><Calendar />2026-08-31</time>
          <button class="icon-button" aria-label="查看通知"><Bell /><b>3</b></button>
          <button class="profile"><span>李</span><strong>李四</strong><ArrowRight /></button>
        </div>
      </header>

      <section class="content">
        <header class="page-head">
          <div>
            <p>今日工作台</p>
            <h1>农户工作台</h1>
            <span>演示农场 · 2 个授权地块</span>
          </div>
          <button class="quiet-button"><Grid />查看我的地块</button>
        </header>

        <section class="dashboard-grid">
          <article class="panel tasks-panel">
            <div class="panel-head">
              <div><h2>今日农事</h2><p>今日暂无计划农事</p></div>
              <button class="text-link">农事日历 <ArrowRight /></button>
            </div>

            <div class="empty-work">
              <span class="calendar-mark"><Calendar /></span>
              <strong>今天可安排现场巡查</strong>
              <small>明日有 2 项墒情巡查</small>
            </div>

            <div class="next-task">
              <span class="task-date"><small>09</small><strong>01</strong></span>
              <div><b>明日待办 · 2 项墒情巡查</b><span>一号田地、二号田地</span></div>
              <button aria-label="查看明日农事"><ArrowRight /></button>
            </div>
          </article>

          <article class="panel action-panel">
            <div class="panel-head">
              <div><h2>待处置</h2><p>2 个事项影响灌溉安排</p></div>
              <span class="attention-count">2</span>
            </div>
            <div class="action-list">
              <div v-for="item in irrigationActions" :key="item.plot" class="action-row">
                <span class="attention-icon"><WarningFilled /></span>
                <div class="action-copy"><b>{{ item.plot }} · 墒情低于阶段下限</b><span>{{ item.moisture }} <i></i> {{ item.threshold }}</span></div>
                <button class="action-link">查看灌溉建议 <ArrowRight /></button>
              </div>
            </div>
          </article>
        </section>

        <section class="panel notice-panel">
          <div class="panel-head">
            <div><h2>需要关注</h2><p>不影响当前待处置事项的设备提醒</p></div>
            <button class="text-link">告警中心 <ArrowRight /></button>
          </div>
          <div class="notice-row">
            <span class="notice-icon"><Tools /></span>
            <div><b>一号田地 · 传感器数据配对异常</b><span>缺少配对的传感器数据</span></div>
            <button class="notice-link">查看详情 <ArrowRight /></button>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(body) { margin: 0; min-width: 320px; background: #f4f7f5; font-family: Inter, "Microsoft YaHei", sans-serif; color: #1e312a; }
.prototype-shell { min-height: 100vh; display: flex; background: #f4f7f5; }
.sidebar { position: fixed; inset: 0 auto 0 0; z-index: 2; display: flex; flex-direction: column; width: 238px; padding: 0 10px; color: #eaf5f1; background: linear-gradient(180deg, #153f34, #102f28); }
.brand { display: flex; align-items: center; gap: 12px; height: 80px; padding: 0 7px; border-bottom: 1px solid rgba(255,255,255,.09); overflow: hidden; white-space: nowrap; }
.brand-mark { display: grid; width: 38px; height: 38px; flex: 0 0 38px; place-items: center; border-radius: 12px; color: #103d31; background: #55bd88; font-weight: 800; }
.brand-copy strong, .brand-copy small { display: block; }.brand-copy strong { font-size: 15px; }.brand-copy small { margin-top: 4px; color: #97bbae; font-size: 11px; letter-spacing: 1px; }
.nav { display: grid; gap: 5px; margin-top: 16px; }
.nav-item, .collapse { display: flex; align-items: center; gap: 12px; width: 100%; min-height: 48px; padding: 0 16px; border: 0; border-radius: 10px; color: #bad0c9; background: transparent; font: inherit; font-size: 14px; font-weight: 600; text-align: left; cursor: pointer; }
.nav-item.active { color: #fff; background: #1f7a5b; }
.collapse { height: 56px; margin: auto -10px 0; padding: 0 26px; border-top: 1px solid rgba(255,255,255,.09); border-radius: 0; color: #a9c2ba; }
.workspace { width: calc(100% - 238px); min-height: 100vh; margin-left: 238px; }
.topbar { display: flex; align-items: center; justify-content: flex-end; height: 64px; padding: 0 28px; border-bottom: 1px solid #e3eae6; background: rgba(255, 255, 255, .94); }
.profile, .icon-button, .quiet-button, .text-link, .action-link, .notice-link, .next-task button { display: inline-flex; align-items: center; border: 0; background: transparent; font: inherit; cursor: pointer; }
.topbar-actions { display: flex; align-items: center; gap: 22px; color: #52645d; }
.topbar time { display: inline-flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; }
.icon-button { position: relative; color: #355247; }.icon-button b { position: absolute; top: -9px; right: -10px; display: grid; width: 18px; height: 18px; place-items: center; border-radius: 50%; color: #fff; background: #d85d4a; font-size: 10px; }
.profile { gap: 9px; color: #29443a; }.profile > span { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 50%; color: #fff; background: #1f7a5b; font-size: 14px; }.profile strong { font-size: 14px; }
.content { max-width: 1360px; padding: 46px 48px 56px; margin: 0 auto; }
.page-head { display: flex; align-items: end; justify-content: space-between; margin-bottom: 26px; }.page-head p { margin: 0 0 7px; color: #277d5b; font-size: 13px; font-weight: 750; }.page-head h1 { margin: 0; color: #18352a; font-size: 30px; letter-spacing: 0; }.page-head span { display: block; margin-top: 8px; color: #73857d; font-size: 14px; }
.quiet-button { gap: 8px; padding: 10px 13px; border: 1px solid #d7e4dc; border-radius: 7px; color: #2c785b; background: #fff; font-size: 13px; font-weight: 650; }
.dashboard-grid { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(420px, .85fr); gap: 20px; }.panel { border: 1px solid #dfe8e3; border-radius: 8px; background: #fff; box-shadow: 0 10px 25px rgba(24, 60, 46, .035); }.tasks-panel, .action-panel { min-height: 365px; padding: 25px; }.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }.panel-head h2 { margin: 0; color: #213c32; font-size: 18px; }.panel-head p { margin: 7px 0 0; color: #84948d; font-size: 13px; }.text-link { gap: 3px; color: #20775b; font-size: 13px; font-weight: 700; white-space: nowrap; }
.empty-work { display: grid; place-items: center; align-content: center; min-height: 191px; padding: 8px 0; text-align: center; }.calendar-mark { display: grid; width: 58px; height: 58px; place-items: center; margin-bottom: 12px; border-radius: 50%; color: #2e8b66; background: #e9f5ee; }.empty-work strong { color: #334e43; font-size: 15px; }.empty-work small { margin-top: 7px; color: #899991; font-size: 12px; }
.next-task { display: grid; grid-template-columns: 42px 1fr 24px; align-items: center; gap: 12px; padding-top: 17px; border-top: 1px solid #e8eeeb; }.task-date { display: grid; align-content: center; height: 42px; border: 1px solid #d4e7dc; border-radius: 7px; color: #267759; background: #f6fbf8; text-align: center; line-height: 1; }.task-date small { font-size: 10px; }.task-date strong { margin-top: 3px; font-size: 15px; }.next-task b, .next-task span { display: block; }.next-task b { color: #2a453a; font-size: 13px; }.next-task span { margin-top: 5px; color: #899890; font-size: 12px; }.next-task button { justify-content: center; color: #6a8277; }
.attention-count { display: grid; width: 28px; height: 28px; place-items: center; border-radius: 50%; color: #aa651d; background: #fff0da; font-size: 13px; font-weight: 750; }.action-list { margin-top: 23px; border-top: 1px solid #e8eeeb; }.action-row { display: grid; grid-template-columns: 32px 1fr auto; align-items: center; gap: 12px; min-height: 112px; border-bottom: 1px solid #e8eeeb; }.attention-icon { display: grid; width: 32px; height: 32px; place-items: center; border-radius: 8px; color: #b86e20; background: #fff1df; }.action-copy b, .action-copy span { display: block; }.action-copy b { color: #2a4238; font-size: 14px; }.action-copy span { margin-top: 8px; color: #7d8e86; font-size: 13px; }.action-copy i { display: inline-block; width: 3px; height: 3px; margin: 0 7px 3px; border-radius: 50%; background: #a2b1aa; }.action-link { gap: 3px; padding: 8px 10px; border: 1px solid #ed9b42; border-radius: 6px; color: #bc6d1d; font-size: 12px; font-weight: 700; white-space: nowrap; }
.notice-panel { margin-top: 20px; padding: 25px; }.notice-row { display: grid; grid-template-columns: 40px 1fr auto; align-items: center; gap: 13px; margin-top: 22px; padding: 16px 0 0; border-top: 1px solid #e8eeeb; }.notice-icon { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 8px; color: #b86e20; background: #fff3e4; }.notice-row b, .notice-row span { display: block; }.notice-row b { color: #2b463a; font-size: 14px; }.notice-row span { margin-top: 6px; color: #83948b; font-size: 13px; }.notice-link { gap: 3px; color: #b66c20; font-size: 13px; font-weight: 700; }
@media (max-width: 1020px) { .sidebar { width: 72px; }.brand { justify-content: center; padding: 0; }.brand-copy, .nav-item span, .collapse span { display: none; }.nav-item, .collapse { justify-content: center; padding: 0; }.collapse { margin: auto -10px 0; }.workspace { width: calc(100% - 72px); margin-left: 72px; }.dashboard-grid { grid-template-columns: 1fr; }.content { padding: 32px 28px; }.topbar { padding: 0 28px; } }
@media (max-width: 680px) { .topbar { height: 64px; padding: 0 18px; }.topbar time, .profile strong, .profile svg { display: none; }.topbar-actions { gap: 17px; }.content { padding: 26px 18px 40px; }.page-head { align-items: flex-start; flex-direction: column; }.page-head h1 { font-size: 25px; }.quiet-button { width: 100%; justify-content: center; }.tasks-panel, .action-panel, .notice-panel { padding: 19px; }.dashboard-grid { gap: 14px; }.action-row { grid-template-columns: 32px 1fr; padding: 17px 0; }.action-link { grid-column: 2; justify-self: start; }.notice-row { grid-template-columns: 40px 1fr; }.notice-link { grid-column: 2; justify-self: start; }.panel-head { align-items: flex-start; }.text-link { padding-top: 2px; } }
</style>
