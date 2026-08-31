import { createRouter, createWebHistory } from 'vue-router'
import { ROLE_HOME, useUserStore } from '@/stores/user'

const routes = [
  //默认重定向到login
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: () => import('@/views/login/Login.vue'), meta: { public: true } },
  { path: '/register', redirect: '/activation' },
  { path: '/activation', name: 'activation', component: () => import('@/views/login/Activation.vue'), meta: { public: true, title: '员工账号激活' } },
  {
    path: '/farmer', component: () => import('@/layout/FarmerLayout.vue'), meta: { role: 'farmer' },
    redirect: '/farmer/dashboard',
    children: [
      { path: 'dashboard', name: 'farmer-dashboard', component: () => import('@/views/farmer/Dashboard.vue'), meta: { title: '我的果园' } },
      { path: 'management', name: 'farmer-management', component: () => import('@/views/farmer/PlotManagement.vue'), meta: { title: '地块管理' } },
      { path: 'plan', name: 'farmer-plan', component: () => import('@/views/farmer/Plan.vue'), meta: { title: '管理计划' } },
      { path: 'tasks', redirect: '/farmer/calendar' },
      { path: 'calendar', name: 'farmer-calendar', component: () => import('@/views/farmer/Calendar.vue'), meta: { title: '农事日历' } },
      { path: 'irrigation', name: 'farmer-irrigation', component: () => import('@/views/farmer/Irrigation.vue'), meta: { title: '智慧灌溉' } },
      { path: 'alarm', name: 'farmer-alarm', component: () => import('@/views/farmer/Alarm.vue'), meta: { title: '告警中心' } },
      { path: 'ai', name: 'farmer-ai', component: () => import('@/views/farmer/AiAssistant.vue'), meta: { title: '小橙子·农事助手' } },
    ],
  },
  {
    path: '/farm', component: () => import('@/layout/FarmAdminLayout.vue'), meta: { role: 'farmAdmin' },
    redirect: '/farm/dashboard',
    children: [
      { path: 'dashboard', name: 'farm-dashboard', component: () => import('@/views/farmAdmin/Dashboard.vue'), meta: { title: '多地块总览' } },
      { path: 'status', name: 'farm-status', component: () => import('@/views/farmAdmin/DeviceControl.vue'), meta: { title: '设备状态' } },
      { path: 'control', redirect: '/farm/status' },
      { path: 'devices', name: 'farm-devices', component: () => import('@/views/farmAdmin/Devices.vue'), meta: { title: '设备管理' } },
      { path: 'alerts', name: 'farm-alerts', component: () => import('@/views/farmAdmin/Alerts.vue'), meta: { title: '告警日志' } },
    ],
  },
  {
    path: '/admin', component: () => import('@/layout/SystemAdminLayout.vue'), meta: { role: 'systemAdmin' },
    redirect: '/admin/dashboard',
    children: [
      { path: 'dashboard', name: 'admin-dashboard', component: () => import('@/views/systemAdmin/Dashboard.vue'), meta: { title: '运行概况' } },
      { path: 'alerts', name: 'admin-alerts', component: () => import('@/views/systemAdmin/Alerts.vue'), meta: { title: '全局告警' } },
      { path: 'users', name: 'admin-users', component: () => import('@/views/systemAdmin/Users.vue'), meta: { title: '用户管理' } },
      { path: 'farm-archives', name: 'admin-farm-archives', component: () => import('@/views/systemAdmin/FarmArchives.vue'), meta: { title: '橙园档案' } },
      { path: 'plot-archives', name: 'admin-plot-archives', component: () => import('@/views/systemAdmin/PlotArchives.vue'), meta: { title: '地块档案' } },
      { path: 'employees', name: 'admin-employees', component: () => import('@/views/systemAdmin/EmployeeManagement.vue'), meta: { title: '员工导入' } },
      { path: 'cultivation-templates', name: 'admin-cultivation-templates', component: () => import('@/views/systemAdmin/CultivationTemplates.vue'), meta: { title: '脐橙管理模板' } },
      { path: 'settings', name: 'admin-settings', component: () => import('@/views/systemAdmin/Settings.vue'), meta: { title: '系统参数' } },
      { path: 'logs', name: 'admin-logs', component: () => import('@/views/systemAdmin/Logs.vue'), meta: { title: '操作日志' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const store = useUserStore()
  if (to.meta.public) return store.isLoggedIn ? ROLE_HOME[store.role] : true
  if (!store.isLoggedIn) return { name: 'login', query: { redirect: to.fullPath } }
  const requiredRole = to.matched.find((record) => record.meta.role)?.meta.role
  if (requiredRole && !store.roles.includes(requiredRole)) return ROLE_HOME[store.role]
  if (requiredRole && requiredRole !== store.role) store.switchRole(requiredRole)
  return true
})

router.afterEach((to) => { document.title = `${to.meta.title || '登录'} - 橙心如意` })

export default router
