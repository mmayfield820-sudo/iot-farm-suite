import { createRouter, createWebHistory } from 'vue-router'
import { ROLE_HOME, useUserStore } from '@/stores/user'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/prototype/farmer-dashboard', name: 'prototype-farmer-dashboard', component: () => import('@/views/prototype/FarmerDashboardPrototype.vue'), meta: { prototype: true, title: '农户首页原型' } },
  { path: '/login', name: 'login', component: () => import('@/views/login/Login.vue'), meta: { public: true } },
  {
    path: '/farmer', component: () => import('@/layout/FarmerLayout.vue'), meta: { role: 'farmer' },
    redirect: '/farmer/dashboard',
    children: [
      { path: 'dashboard', name: 'farmer-dashboard', component: () => import('@/views/farmer/Dashboard.vue'), meta: { title: '农场首页' } },
      { path: 'management', name: 'farmer-management', component: () => import('@/views/farmer/PlotManagement.vue'), meta: { title: '地块管理' } },
      { path: 'plan', name: 'farmer-plan', component: () => import('@/views/farmer/Plan.vue'), meta: { title: '管理计划' } },
      { path: 'tasks', name: 'farmer-tasks', component: () => import('@/views/farmer/Tasks.vue'), meta: { title: '我的农事' } },
      { path: 'monitor', name: 'farmer-monitor', redirect: (to) => ({ path: '/farmer/management', query: { ...to.query, tab: 'monitor' } }) },
      { path: 'history', name: 'farmer-history', redirect: (to) => ({ path: '/farmer/management', query: { ...to.query, tab: 'history' } }) },
      { path: 'irrigation', name: 'farmer-irrigation', component: () => import('@/views/farmer/Irrigation.vue'), meta: { title: '智慧灌溉' } },
      { path: 'alarm', name: 'farmer-alarm', component: () => import('@/views/farmer/Alarm.vue'), meta: { title: '告警中心' } },
      { path: 'ai', name: 'farmer-ai', component: () => import('@/views/farmer/AiAssistant.vue'), meta: { title: '小橙子·农事助手' } },
    ],
  },
  {
    path: '/farm', component: () => import('@/layout/FarmAdminLayout.vue'), meta: { role: 'farmAdmin' },
    redirect: '/farm/dashboard',
    children: [
      { path: 'dashboard', name: 'farm-dashboard', component: () => import('@/views/farmAdmin/Dashboard.vue'), meta: { title: '地块总览' } },
      { path: 'device-monitoring-management', name: 'farm-device-monitoring-management', component: () => import('@/views/farmAdmin/DeviceMonitoringManagement.vue'), meta: { title: '设备监测与管理' } },
      { path: 'status', redirect: '/farm/device-monitoring-management' },
      { path: 'control', redirect: '/farm/device-monitoring-management' },
      { path: 'devices', redirect: '/farm/device-monitoring-management' },
      { path: 'alerts', name: 'farm-alerts', component: () => import('@/views/farmAdmin/Alerts.vue'), meta: { title: '告警日志' } },
      { path: 'records', name: 'farm-records', component: () => import('@/views/farmAdmin/ManagementRecords.vue'), meta: { title: '生产档案' } },
      { path: 'production', name: 'farm-production', component: () => import('@/views/farmAdmin/Production.vue'), meta: { title: '年度生产管理计划' } },
      { path: 'cycle-draft', name: 'farm-cycle-draft', component: () => import('@/views/farmAdmin/CycleDraft.vue'), meta: { title: '下一年度管理计划' } },
    ],
  },
  {
    path: '/admin', component: () => import('@/layout/SystemAdminLayout.vue'), meta: { role: 'systemAdmin' },
    redirect: '/admin/archives',
    children: [
      { path: 'archives', name: 'admin-archives', component: () => import('@/views/systemAdmin/Dashboard.vue'), meta: { title: '基础档案' } },
      { path: 'dashboard', redirect: '/admin/archives' },
      { path: 'alerts', name: 'admin-alerts', component: () => import('@/views/systemAdmin/Alerts.vue'), meta: { title: '全局告警' } },
      { path: 'users', name: 'admin-users', component: () => import('@/views/systemAdmin/Users.vue'), meta: { title: '用户管理' } },
      { path: 'templates', name: 'admin-templates', component: () => import('@/views/systemAdmin/Templates.vue'), meta: { title: '品种模板' } },
      { path: 'logs', name: 'admin-logs', component: () => import('@/views/systemAdmin/Logs.vue'), meta: { title: '操作日志' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const store = useUserStore()
  if (to.meta.prototype) return true
  if (to.meta.public) return store.isLoggedIn ? ROLE_HOME[store.role] : true
  if (!store.isLoggedIn) return { name: 'login', query: { redirect: to.fullPath } }
  const requiredRole = to.matched.find((record) => record.meta.role)?.meta.role
  if (requiredRole && !store.roles.includes(requiredRole)) return ROLE_HOME[store.role]
  if (requiredRole && requiredRole !== store.role) store.switchRole(requiredRole)
  return true
})

router.afterEach((to) => { document.title = `${to.meta.title || '登录'} - 智慧农业监测平台` })

export default router
