<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ROLE_LABEL, useUserStore } from '@/stores/user'
import { useFarmerStore } from '@/stores/farmer'
import { usePlatformStore } from '@/stores/platform'
import { useFarmAdminStore } from '@/stores/farmAdmin'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const props = defineProps({ title: String, subtitle: String, menu: Array, contextLabel: { type: String, default: '朱衣橙园' }, contextStatus: { type: String, default: '运行正常' }, contextStatusTone: { type: String, default: 'success' }, showContext: { type: Boolean, default: true }, hideContextPaths: { type: Array, default: () => [] }, accent: { type: String, default: '#df741b' } })
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
async function openOrToggleAssistant() {
  if (route.path !== '/farmer/ai') {
    await router.push('/farmer/ai')
    await nextTick()
    window.setTimeout(() => window.dispatchEvent(new CustomEvent('orchard-assistant-toggle-voice')), 100)
  } else {
    window.dispatchEvent(new CustomEvent('orchard-assistant-toggle-voice'))
  }
}
</script>

<template>
  <div class="shell" :style="{ '--accent': accent, '--el-color-primary': accent }">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand"><div class="brand-mark">橙</div><div v-if="!collapsed"><strong>{{ title }}</strong><span>{{ subtitle }}</span></div></div>
      <el-menu :default-active="activePath" router class="nav" :collapse="collapsed" :collapse-transition="false">
        <el-menu-item v-for="item in menu" :key="item.path" :index="item.path">
          <el-icon><component :is="icon(item.icon)" /></el-icon><template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>
      <button v-if="userStore.role === 'farmer'" class="sidebar-mascot" :class="{ collapsed, active: route.path === '/farmer/ai' }" type="button" title="打开小橙子农事助手" @click="openOrToggleAssistant">
        <span class="sidebar-orange"><i class="leaf"></i><i class="eye eye-left"></i><i class="eye eye-right"></i><i class="mouth"></i><i class="cheek cheek-left"></i><i class="cheek cheek-right"></i></span>
        <span v-if="!collapsed" class="sidebar-mascot-copy"><strong>小橙子</strong><small>{{ route.path === '/farmer/ai' ? '点一下和我说话' : '农事助手' }}</small></span>
      </button>
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
              <div class="font-preview"><span>预览</span><p>橙心如意，让橙园管理更轻松</p><em>当前 {{ fontSize }}px</em></div>
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
.sidebar { width: 238px; position: fixed; inset: 0 auto 0 0; z-index: 10; display: flex; flex-direction: column; color: #fff4e8; background: linear-gradient(180deg, #4c2a18, #2d1b12); transition: width .2s; }
.sidebar.collapsed { width: 72px; }
.brand { height: 80px; display: flex; align-items: center; gap: 12px; padding: 0 17px; border-bottom: 1px solid rgba(255,255,255,.09); overflow: hidden; white-space: nowrap; }
.brand-mark { width: 38px; height: 38px; flex: 0 0 38px; display: grid; place-items: center; border-radius: 12px; background: linear-gradient(145deg, #ffad49, #ef7d1e); font-weight: 800; color: #4a2816; box-shadow: 0 8px 20px rgba(9,4,1,.2); }
.brand strong, .brand span { display: block; }.brand strong { font-size: 15px; }.brand span { margin-top: 4px; color: #d7bca7; font-size: 11px; letter-spacing: 1px; }
.nav { flex: 1; padding: 16px 10px; border: 0; background: transparent; }
.nav :deep(.el-menu-item) { height: 48px; margin-bottom: 5px; border-radius: 10px; color: #dbc6b6; }
.nav :deep(.el-menu-item:hover) { background: rgba(255,255,255,.08); color: white; }
.nav :deep(.el-menu-item.is-active) { color: white; background: var(--accent); }
.collapse-btn { height: 56px; border: 0; border-top: 1px solid rgba(255,255,255,.09); background: transparent; color: #d3bba9; display: flex; align-items: center; gap: 12px; padding: 0 26px; cursor: pointer; white-space: nowrap; }
.workspace { min-width: 0; flex: 1; margin-left: 238px; transition: margin .2s; }.sidebar.collapsed + .workspace { margin-left: 72px; }
.topbar { height: 64px; padding: 0 28px; display: flex; justify-content: space-between; align-items: center; background: rgba(255,253,249,.95); border-bottom: 1px solid var(--line); color: #6d584a; position: sticky; top: 0; z-index: 5; }
.topbar.context-hidden { justify-content: flex-end; }
.farm-dot { width: 8px; height: 8px; display: inline-block; margin-right: 7px; border-radius: 50%; background: #39ae75; box-shadow: 0 0 0 4px #dff4e9; }.online { margin-left: 10px; padding: 4px 8px; border-radius: 9px; font-size: 12px; }.online.success{color:#2a875f;background:#e9f7f0}.online.info{color:#267f99;background:#e7f5f8}.online.warning{color:#a46823;background:#fff3df}.online.danger{color:#b84d4d;background:#fdecec}
.user-area { display: flex; align-items: center; gap: 10px; }.avatar { width: 32px; height: 32px; display: grid; place-items: center; border-radius: 50%; color: white; background: var(--accent); }
.notification-btn{width:34px;height:34px;display:grid;place-items:center;border:1px solid var(--line);border-radius:10px;color:#725643;background:#fff9f3;cursor:pointer}.notification-btn:hover{border-color:var(--accent);color:var(--accent)}
.font-trigger{width:38px;height:34px;display:flex;align-items:baseline;justify-content:center;gap:2px;border:1px solid var(--line);border-radius:10px;color:#704b32;background:#fff9f3;cursor:pointer;transition:.2s}.font-trigger:hover{border-color:var(--accent);color:var(--accent);background:#fff1e4}.font-trigger span{font-size:16px;font-weight:700}.font-trigger .font-small{font-size:10px;font-weight:600}.font-control{padding:2px}.font-control-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.font-control-head strong,.font-control-head small{display:block}.font-control-head strong{color:#59351f;font-size:14px}.font-control-head small{margin-top:4px;color:#9a897e;font-size:11px}.font-slider{display:grid;grid-template-columns:18px 1fr 18px;align-items:center;gap:10px;margin:18px 2px 14px;color:#806f64;font-size:11px}.font-preview{position:relative;padding:12px 13px;border:1px solid #f0dfd0;border-radius:11px;background:#fff8f0}.font-preview span{color:#a28d7e;font-size:10px}.font-preview p{margin:5px 0 0;color:#694126;font-size:var(--app-font-size);font-weight:600}.font-preview em{position:absolute;right:10px;top:10px;color:#b0642e;font-size:10px;font-style:normal}
.role-switch { display: flex; align-items: center; gap: 6px; padding: 7px 11px; border: 1px solid var(--line); border-radius: 9px; color: #65452f; background: #fff9f3; cursor: pointer; }.role-switch:hover { border-color: var(--accent); color: var(--accent); }.single-role { padding: 6px 9px; border-radius: 8px; color: var(--accent); background: #fff1e4; font-size: 13px; }.current-role { color: var(--accent); font-weight: 600; }
.content { padding: 28px; }
@media (max-width: 900px) { .sidebar { width: 72px; }.sidebar .brand > div:last-child, .collapse-btn span, .nav :deep(.el-menu-item span) { display: none; }.nav :deep(.el-menu-item) { justify-content: center; padding: 0 !important; }.workspace { margin-left: 72px; }.topbar { padding: 0 16px; }.topbar > div:first-child, .display-name { display:none; }.content { padding: 18px; } }

/* 网页13的轻透果园底色，仅调整外壳，不触碰页面业务组件。 */
.shell{color:#3f3129;background:#f5f1e8}.sidebar{overflow:hidden;color:#565a52;background:rgba(247,242,231,.965);border-right:1px solid #e0d8c9;box-shadow:8px 0 30px rgba(72,62,49,.045);backdrop-filter:blur(10px)}.sidebar::before,.sidebar::after{position:absolute;z-index:0;inset:auto;content:'';pointer-events:none;background:url('../assets/orchard-linework.svg') no-repeat}.sidebar::before{left:-300px;bottom:-105px;width:760px;height:500px;background-position:left bottom;background-size:760px auto;opacity:.48}.sidebar::after{right:-520px;top:-245px;width:980px;height:620px;background-position:right top;background-size:980px auto;opacity:.2}.sidebar>*{position:relative;z-index:1}.brand{border-bottom-color:#e8e0d3}.brand-mark{color:#a76528;background:#f2e7d5;border:1px solid #e6d7bf;box-shadow:0 5px 14px rgba(103,78,47,.08)}.brand strong{color:#4d4b43}.brand span{color:#9b958a}.nav :deep(.el-menu-item){color:#706e66}.nav :deep(.el-menu-item:hover){color:#3f6f58;background:#f2f5ed}.nav :deep(.el-menu-item.is-active){color:#3d7658;background:#eaf3e8;box-shadow:inset 3px 0 0 #5f956f}.collapse-btn{color:#8b887f;border-top-color:#e6dfd3}.topbar{height:68px;color:#5d6a63;background:rgba(255,254,250,.88);backdrop-filter:blur(12px)}.content{position:relative;max-width:1680px;width:100%;margin:0 auto;padding:30px}.content::before{position:fixed;z-index:0;inset:68px 0 0 238px;content:'';pointer-events:none;background:url('../assets/orchard-linework.svg') center / cover no-repeat,radial-gradient(circle at 82% 88%,rgba(232,137,45,.055),transparent 28%),radial-gradient(circle at 12% 18%,rgba(92,137,100,.04),transparent 24%),linear-gradient(135deg,rgba(255,255,255,.18),transparent 42%);opacity:.34}.content>*{position:relative;z-index:1}.sidebar.collapsed~.workspace .content::before{left:72px}
.sidebar-mascot{position:relative;width:100%;min-height:92px;display:flex;align-items:center;justify-content:center;gap:10px;padding:8px 14px;border:0;color:#5f6e65;background:transparent;cursor:pointer;text-align:left;transition:.2s}.sidebar-mascot:hover,.sidebar-mascot.active{background:rgba(255,255,255,.15)}.sidebar-mascot.collapsed{min-height:82px;padding:7px 0}.sidebar-mascot-copy{display:flex;flex-direction:column;min-width:0}.sidebar-mascot-copy strong{color:#52665c;font-size:13px}.sidebar-mascot-copy small{margin-top:3px;color:#9a9489;font-size:10px}.sidebar-orange{position:relative;display:block;width:66px;height:66px;flex:0 0 66px;border-radius:48% 52% 50% 50%;background:#e4a04e;box-shadow:inset -6px -8px 0 rgba(145,91,39,.09),0 8px 16px rgba(112,78,44,.09);transition:.22s}.sidebar-mascot:hover .sidebar-orange{transform:translateY(-2px) rotate(-1deg)}.sidebar-orange .leaf{position:absolute;right:4px;top:-7px;width:22px;height:10px;border:1px solid #506d58;border-radius:100% 0 100% 0;background:#66876d;transform:rotate(-23deg)}.sidebar-orange .eye{position:absolute;top:25px;width:6px;height:9px;border-radius:50%;background:#5b463c}.sidebar-orange .eye-left{left:19px}.sidebar-orange .eye-right{right:19px}.sidebar-orange .mouth{position:absolute;left:27px;top:39px;width:13px;height:8px;border-bottom:2px solid #674b3d;border-radius:0 0 50% 50%}.sidebar-orange .cheek{position:absolute;top:39px;width:8px;height:5px;border-radius:50%;background:rgba(190,83,56,.24)}.sidebar-orange .cheek-left{left:11px}.sidebar-orange .cheek-right{right:11px}.sidebar-mascot.active .sidebar-orange{animation:mascot-breathe 1.7s ease-in-out infinite}.sidebar-mascot.collapsed .sidebar-mascot-copy{display:none}@keyframes mascot-breathe{50%{transform:translateY(-3px) rotate(1deg)}}
@media(max-width:900px){.content::before{left:72px}.sidebar-mascot-copy{display:none}.sidebar-mascot{padding:7px 0}.sidebar-orange{width:58px;height:58px;flex-basis:58px}.sidebar-orange .eye{top:22px}.sidebar-orange .eye-left{left:17px}.sidebar-orange .eye-right{right:17px}.sidebar-orange .mouth{left:24px;top:34px}}
</style>
