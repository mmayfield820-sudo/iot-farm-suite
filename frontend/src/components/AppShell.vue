<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ROLE_LABEL, useUserStore } from '@/stores/user'
import { useFarmerStore } from '@/stores/farmer'
import { usePlatformStore } from '@/stores/platform'
import { useFarmAdminStore } from '@/stores/farmAdmin'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const props = defineProps({ title: String, subtitle: String, menu: Array, contextLabel: { type: String, default: '一号示范农场' }, contextStatus: { type: String, default: '运行正常' }, contextStatusTone: { type: String, default: 'success' }, showContext: { type: Boolean, default: true }, hideContextPaths: { type: Array, default: () => [] }, accent: { type: String, default: '#1f7a5b' } })
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const farmerStore = useFarmerStore()
const platformStore = usePlatformStore()
const farmAdminStore = useFarmAdminStore()
const collapsed = ref(false)
const fontSize = ref(Number(localStorage.getItem('smart-farm-font-size')) || 14)
const activePath = computed(() => route.path)
const contextVisible = computed(() => props.showContext && !props.hideContextPaths.includes(route.path))
const roleOptions = computed(() => userStore.roles.map((value) => ({ value, label: ROLE_LABEL[value] || value })))
const notificationTarget = computed(() => userStore.role === 'farmer' ? '/farmer/alarm' : userStore.role === 'farmAdmin' ? '/farm/alerts' : '/admin/alerts')
const notificationCount = computed(() => {
  if (userStore.role === 'farmer') return farmerStore.unhandledCount
  if (userStore.role === 'farmAdmin') {
    return farmAdminStore.visibleAlerts.filter((alert) => alert.status === '未处理').length
  }
  return platformStore.unhandledAlerts
})

function icon(name) { return ElementPlusIconsVue[name] }
function applyFontSize(size) {
  const root = document.documentElement
  root.style.setProperty('--app-font-size', `${size}px`)
  root.style.setProperty('--app-font-small', `${Math.max(10, size - 2)}px`)
  root.style.setProperty('--app-font-tiny', `${Math.max(9, size - 3)}px`)
  root.style.setProperty('--app-font-heading', `${size + 2}px`)
  root.style.setProperty('--app-font-title', `${size + 11}px`)
  root.style.setProperty('--app-font-metric', `${size + 11}px`)
}
watch(fontSize, (size) => {
  localStorage.setItem('smart-farm-font-size', String(size))
  applyFontSize(size)
}, { immediate: true })
function resetFontSize() { fontSize.value = 14 }
async function changeRole(nextRole) {
  if (nextRole === userStore.role) return
  const home = userStore.switchRole(nextRole)
  await router.push(home)
}
function signOut() { userStore.logout(); router.replace('/login') }
function openNotifications() { router.push(notificationTarget.value) }
</script>

<template>
  <div class="shell" :style="{ '--accent': accent, '--el-color-primary': accent }">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand"><div class="brand-mark">禾</div><div v-if="!collapsed"><strong>{{ title }}</strong><span>{{ subtitle }}</span></div></div>
      <el-menu :default-active="activePath" router class="nav" :collapse="collapsed" :collapse-transition="false">
        <el-menu-item v-for="item in menu" :key="item.path" :index="item.path">
          <el-icon><component :is="icon(item.icon)" /></el-icon><template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>
      <button class="collapse-btn" @click="collapsed = !collapsed"><el-icon><component :is="collapsed ? icon('Expand') : icon('Fold')" /></el-icon><span v-if="!collapsed">收起菜单</span></button>
    </aside>
    <section class="workspace">
      <header class="topbar" :class="{ 'context-hidden': !contextVisible }">
        <div v-if="contextVisible"><slot name="context"><span class="farm-dot"></span> {{ contextLabel }} <span :class="['online', contextStatusTone]">{{ contextStatus }}</span></slot></div>
        <div class="user-area">
          <el-popover placement="bottom" :width="284" trigger="click" popper-class="font-size-popover">
            <template #reference><button class="font-trigger" title="调节字体大小"><span class="font-small">A</span><span>A</span></button></template>
            <div class="font-control">
              <div class="font-control-head"><div><strong>页面字体大小</strong><small>拖动滑杆即可实时调整</small></div><el-button text size="small" @click="resetFontSize">恢复默认</el-button></div>
              <div class="font-slider"><span>小</span><el-slider v-model="fontSize" :min="12" :max="18" :step="1" :show-tooltip="true" :format-tooltip="(value) => `${value}px`"/><span>大</span></div>
              <div class="font-preview"><span>预览</span><p>智慧农业，让管理更轻松</p><em>当前 {{ fontSize }}px</em></div>
            </div>
          </el-popover>
          <el-badge :value="notificationCount" :hidden="!notificationCount" :max="99"><button class="notification-btn" title="查看未处理告警" @click="openNotifications"><el-icon><component :is="icon('Bell')" /></el-icon></button></el-badge>
          <el-dropdown v-if="roleOptions.length > 1" trigger="click" @command="changeRole">
            <button class="role-switch">
              <span>{{ ROLE_LABEL[userStore.role] }}</span>
              <el-icon><component :is="icon('ArrowDown')" /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="item in roleOptions" :key="item.value" :command="item.value" :class="{ 'current-role': item.value === userStore.role }">
                  <el-icon><component :is="item.value === userStore.role ? icon('Check') : icon('User')" /></el-icon>{{ item.label }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <span v-else class="single-role">{{ ROLE_LABEL[userStore.role] }}</span>
          <div class="avatar">{{ userStore.user?.displayName?.slice(0, 1)?.toUpperCase() }}</div>
          <span class="display-name">{{ userStore.user?.displayName }}</span>
          <el-button text @click="signOut">退出</el-button>
        </div>
      </header>
      <main class="content"><router-view /></main>
    </section>
  </div>
</template>

<style scoped>
.shell { min-height: 100vh; display: flex; }
.sidebar { width: 238px; position: fixed; inset: 0 auto 0 0; z-index: 10; display: flex; flex-direction: column; color: #eaf5f1; background: linear-gradient(180deg, #153f34, #102f28); transition: width .2s; }
.sidebar.collapsed { width: 72px; }
.brand { height: 80px; display: flex; align-items: center; gap: 12px; padding: 0 17px; border-bottom: 1px solid rgba(255,255,255,.09); overflow: hidden; white-space: nowrap; }
.brand-mark { width: 38px; height: 38px; flex: 0 0 38px; display: grid; place-items: center; border-radius: 12px; background: #55bd88; font-weight: 800; color: #103d31; }
.brand strong, .brand span { display: block; }.brand strong { font-size: 15px; }.brand span { margin-top: 4px; color: #97bbae; font-size: 11px; letter-spacing: 1px; }
.nav { flex: 1; padding: 16px 10px; border: 0; background: transparent; }
.nav :deep(.el-menu-item) { height: 48px; margin-bottom: 5px; border-radius: 10px; color: #bad0c9; }
.nav :deep(.el-menu-item:hover) { background: rgba(255,255,255,.08); color: white; }
.nav :deep(.el-menu-item.is-active) { color: white; background: var(--accent); }
.collapse-btn { height: 56px; border: 0; border-top: 1px solid rgba(255,255,255,.09); background: transparent; color: #a9c2ba; display: flex; align-items: center; gap: 12px; padding: 0 26px; cursor: pointer; white-space: nowrap; }
.workspace { min-width: 0; flex: 1; margin-left: 238px; transition: margin .2s; }.sidebar.collapsed + .workspace { margin-left: 72px; }
.topbar { height: 64px; padding: 0 28px; display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,.95); border-bottom: 1px solid var(--line); color: #4d625a; position: sticky; top: 0; z-index: 5; }
.topbar.context-hidden { justify-content: flex-end; }
.farm-dot { width: 8px; height: 8px; display: inline-block; margin-right: 7px; border-radius: 50%; background: #39ae75; box-shadow: 0 0 0 4px #dff4e9; }.online { margin-left: 10px; padding: 4px 8px; border-radius: 9px; font-size: 12px; }.online.success{color:#2a875f;background:#e9f7f0}.online.info{color:#267f99;background:#e7f5f8}.online.warning{color:#a46823;background:#fff3df}.online.danger{color:#b84d4d;background:#fdecec}
.user-area { display: flex; align-items: center; gap: 10px; }.avatar { width: 32px; height: 32px; display: grid; place-items: center; border-radius: 50%; color: white; background: var(--accent); }
.notification-btn{width:34px;height:34px;display:grid;place-items:center;border:1px solid var(--line);border-radius:10px;color:#4f6b61;background:#f8fbf9;cursor:pointer}.notification-btn:hover{border-color:var(--accent);color:var(--accent)}
.font-trigger{width:38px;height:34px;display:flex;align-items:baseline;justify-content:center;gap:2px;border:1px solid var(--line);border-radius:10px;color:#426458;background:#f8fbf9;cursor:pointer;transition:.2s}.font-trigger:hover{border-color:var(--accent);color:var(--accent);background:#f0f8f4}.font-trigger span{font-size:16px;font-weight:700}.font-trigger .font-small{font-size:10px;font-weight:600}.font-control{padding:2px}.font-control-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.font-control-head strong,.font-control-head small{display:block}.font-control-head strong{color:#29473d;font-size:14px}.font-control-head small{margin-top:4px;color:#8a9893;font-size:11px}.font-slider{display:grid;grid-template-columns:18px 1fr 18px;align-items:center;gap:10px;margin:18px 2px 14px;color:#70847b;font-size:11px}.font-preview{position:relative;padding:12px 13px;border:1px solid #e2eee8;border-radius:11px;background:#f5faf7}.font-preview span{color:#85a096;font-size:10px}.font-preview p{margin:5px 0 0;color:#315347;font-size:var(--app-font-size);font-weight:600}.font-preview em{position:absolute;right:10px;top:10px;color:#5c927a;font-size:10px;font-style:normal}
.role-switch { display: flex; align-items: center; gap: 6px; padding: 7px 11px; border: 1px solid var(--line); border-radius: 9px; color: #385249; background: #f8fbf9; cursor: pointer; }.role-switch:hover { border-color: var(--accent); color: var(--accent); }.single-role { padding: 6px 9px; border-radius: 8px; color: var(--accent); background: #f0f6f3; font-size: 13px; }.current-role { color: var(--accent); font-weight: 600; }
.content { padding: 28px; }
@media (max-width: 900px) { .sidebar { width: 72px; }.sidebar .brand > div:last-child, .collapse-btn span, .nav :deep(.el-menu-item span) { display: none; }.nav :deep(.el-menu-item) { justify-content: center; padding: 0 !important; }.workspace { margin-left: 72px; }.topbar { padding: 0 16px; }.topbar > div:first-child, .display-name { display:none; }.content { padding: 18px; } }
</style>
