<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { ROLE_LABEL, useUserStore } from '@/stores/user'
import { useFarmerStore } from '@/stores/farmer'
import { usePlatformStore } from '@/stores/platform'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import farmBrandLogo from '@/assets/farm-brand-logo.png'

const props = defineProps({ title: String, subtitle: String, menu: Array, contextLabel: { type: String, default: '一号示范农场' }, contextStatus: { type: String, default: '运行正常' }, contextStatusTone: { type: String, default: 'success' }, contextOptions: { type: Array, default: () => [] }, contextValue: { type: String, default: '' }, allowRoleSwitch: { type: Boolean, default: true }, showContext: { type: Boolean, default: true }, hideContextPaths: { type: Array, default: () => [] }, accent: { type: String, default: '#1f7a5b' } })
const emit = defineEmits(['context-change'])
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const farmerStore = useFarmerStore()
const platformStore = usePlatformStore()
const collapsed = ref(false)
const profileOpen = ref(false)
const profileSaving = ref(false)
const profileForm = reactive({ name: '', email: '', phone: '', avatarData: '', currentPassword: '', newPassword: '', confirmPassword: '' })
const fontSize = ref(Number(localStorage.getItem('smart-farm-font-size')) || 14)
const activePath = computed(() => route.path)
const contextVisible = computed(() => props.showContext && !props.hideContextPaths.includes(route.path))
const roleOptions = computed(() => userStore.roles.map((value) => ({ value, label: ROLE_LABEL[value] || value })))
const profileRoleText = computed(() => userStore.roles.map((value) => ROLE_LABEL[value] || value).join('、') || '暂未分配')
const profileScopeText = computed(() => {
  const details = [
    ...(userStore.user?.farmScopes || []).map((item) => `${item.name || item.id}（${item.id}）`),
    ...(userStore.user?.plotScopes || []).map((item) => `${item.name || item.id}（${item.id}）`),
  ]
  if (details.length) return details.join('、')
  const ids = [...(userStore.user?.roleScopes?.farmAdmin?.farmIds || []), ...(userStore.user?.roleScopes?.farmer?.plotIds || [])]
  return ids.length ? ids.join('、') : '全局权限或暂未分配具体范围'
})
const notificationTarget = computed(() => userStore.role === 'farmer' ? '/farmer/alarm' : userStore.role === 'farmAdmin' ? '/farm/alerts' : '/admin/alerts')
const notificationCount = computed(() => {
  if (userStore.role === 'farmer') return farmerStore.unhandledCount
  if (userStore.role === 'farmAdmin') {
    const scoped = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
    const farmIds = scoped.length ? scoped : platformStore.farms.map((farm) => String(farm.farmId))
    const plotIds = platformStore.plots.filter((plot) => farmIds.includes(String(plot.farmId))).map((plot) => String(plot.plotNo))
    return platformStore.alerts.filter((alert) => alert.status === '未处理' && plotIds.includes(String(alert.plotNo || alert.plotId))).length
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
async function openProfile() {
  try { await userStore.refreshProfile() } catch { ElMessage.warning('最新账号信息加载失败，已显示本地资料') }
  profileForm.name = userStore.user?.displayName || ''
  profileForm.email = userStore.user?.email || ''
  profileForm.phone = userStore.user?.phone || ''
  profileForm.avatarData = userStore.user?.avatarData || ''
  profileForm.currentPassword = ''
  profileForm.newPassword = ''
  profileForm.confirmPassword = ''
  profileOpen.value = true
}
function changeAvatar(uploadFile) {
  const file = uploadFile.raw
  if (!file) return
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
    return ElMessage.warning('请选择 PNG、JPG 或 WebP 图片')
  }
  if (file.size > 5 * 1024 * 1024) return ElMessage.warning('头像原图不能超过 5 MB')
  const reader = new FileReader()
  reader.onload = () => {
    const image = new Image()
    image.onload = () => {
      const scale = Math.min(1, 512 / Math.max(image.width, image.height))
      const canvas = document.createElement('canvas')
      canvas.width = Math.max(1, Math.round(image.width * scale))
      canvas.height = Math.max(1, Math.round(image.height * scale))
      canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height)
      const optimized = canvas.toDataURL('image/webp', 0.88)
      if (optimized.length > 1_400_000) return ElMessage.warning('图片处理后仍然过大，请更换一张图片')
      profileForm.avatarData = optimized
    }
    image.onerror = () => ElMessage.error('图片格式异常，请重新选择')
    image.src = String(reader.result || '')
  }
  reader.onerror = () => ElMessage.error('头像读取失败，请重新选择')
  reader.readAsDataURL(file)
}
async function saveProfile() {
  if (!profileForm.name.trim()) return ElMessage.warning('请填写姓名')
  if (profileForm.newPassword && profileForm.newPassword.length < 6) return ElMessage.warning('新密码至少需要 6 位')
  if (profileForm.newPassword && !profileForm.currentPassword) return ElMessage.warning('请输入当前密码')
  if (profileForm.newPassword !== profileForm.confirmPassword) return ElMessage.warning('两次输入的新密码不一致')
  profileSaving.value = true
  try {
    await userStore.updateProfile({ name: profileForm.name.trim(), email: profileForm.email.trim() || null, phone: profileForm.phone.trim() || null, avatarData: profileForm.avatarData || null, currentPassword: profileForm.newPassword ? profileForm.currentPassword : null, newPassword: profileForm.newPassword || null })
    profileOpen.value = false
    ElMessage.success('个人信息已更新')
  } catch (error) {
    ElMessage.error(error.message || '个人信息更新失败')
  } finally { profileSaving.value = false }
}
function openNotifications() { router.push(notificationTarget.value) }
async function openOrToggleAssistant() {
  if (route.path !== '/farmer/ai') {
    await router.push('/farmer/ai')
    await nextTick()
  }
  window.dispatchEvent(new CustomEvent('orchard-assistant-focus'))
}
</script>

<template>
  <div class="shell" :style="{ '--accent': accent, '--el-color-primary': accent }">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand"><div class="brand-mark" aria-hidden="true"><img :src="farmBrandLogo" alt="" /></div><div v-if="!collapsed"><strong>{{ title }}</strong><span>{{ subtitle }}</span></div></div>
      <el-menu :default-active="activePath" router class="nav" :collapse="collapsed" :collapse-transition="false">
        <el-menu-item v-for="item in menu" :key="item.path" :index="item.path">
          <el-icon><component :is="icon(item.icon)" /></el-icon><template #title>{{ item.label }}</template>
          <span v-if="item.path === notificationTarget && notificationCount" class="menu-alert-count">{{ notificationCount > 99 ? '99+' : notificationCount }}</span>
        </el-menu-item>
      </el-menu>
      <button v-if="userStore.role === 'farmer'" class="sidebar-mascot" :class="{ collapsed, active: route.path === '/farmer/ai' }" type="button" title="打开小橙子农事助手" @click="openOrToggleAssistant">
        <span class="sidebar-orange" aria-hidden="true"><i class="leaf"></i><i class="eye eye-left"></i><i class="eye eye-right"></i><i class="mouth"></i><i class="cheek cheek-left"></i><i class="cheek cheek-right"></i></span>
        <span v-if="!collapsed" class="sidebar-mascot-copy"><strong>小橙子</strong><small>{{ route.path === '/farmer/ai' ? '点击开始提问' : '农事助手' }}</small></span>
      </button>
      <button class="collapse-btn" @click="collapsed = !collapsed"><el-icon><component :is="collapsed ? icon('Expand') : icon('Fold')" /></el-icon><span v-if="!collapsed">收起菜单</span></button>
    </aside>
    <section class="workspace">
      <header class="topbar" :class="{ 'context-hidden': !contextVisible }">
        <div v-if="contextVisible" class="farm-context"><el-icon class="farm-context-icon"><Location /></el-icon><el-select v-if="contextOptions.length" :model-value="contextValue" class="farm-context-select" @change="emit('context-change', $event)"><el-option v-for="item in contextOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select><span v-else>{{ contextLabel }}</span><span :class="['online', contextStatusTone]">{{ contextStatus }}</span></div>
        <div class="user-area">
          <el-popover placement="bottom" :width="284" trigger="click" popper-class="font-size-popover">
            <template #reference><button class="font-trigger" title="调节字体大小"><span class="font-small">A</span><span>A</span></button></template>
            <div class="font-control">
              <div class="font-control-head"><div><strong>页面字体大小</strong><small>拖动滑杆即可实时调整</small></div><el-button text size="small" @click="resetFontSize">恢复默认</el-button></div>
              <div class="font-slider"><span>小</span><el-slider v-model="fontSize" :min="12" :max="18" :step="1" :show-tooltip="true" :format-tooltip="(value) => `${value}px`"/><span>大</span></div>
              <div class="font-preview"><span>预览</span><p>智慧农业，让管理更轻松</p><em>当前 {{ fontSize }}px</em></div>
            </div>
          </el-popover>
          <el-badge class="notification-badge" :value="notificationCount" :hidden="!notificationCount" :max="99"><button class="notification-btn" title="查看未处理告警" @click="openNotifications"><el-icon><component :is="icon('Bell')" /></el-icon></button></el-badge>
          <el-dropdown v-if="allowRoleSwitch && roleOptions.length > 1" trigger="click" @command="changeRole">
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
          <button class="profile-trigger" type="button" title="修改个人信息" @click="openProfile"><span class="avatar"><img v-if="userStore.user?.avatarData" :src="userStore.user.avatarData" alt="个人头像" /><template v-else>{{ userStore.user?.displayName?.slice(0, 1)?.toUpperCase() }}</template></span><span class="display-name">{{ userStore.user?.displayName }}</span></button>
          <el-button text @click="signOut">退出</el-button>
        </div>
      </header>
      <main class="content"><router-view /></main>
    </section>
    <el-dialog v-model="profileOpen" title="个人信息" width="min(680px, calc(100% - 28px))" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="头像">
          <div class="avatar-editor">
            <span class="avatar-preview"><img v-if="profileForm.avatarData" :src="profileForm.avatarData" alt="头像预览" /><template v-else>{{ profileForm.name?.slice(0, 1)?.toUpperCase() || '用' }}</template></span>
            <div class="avatar-actions">
              <el-upload accept="image/png,image/jpeg,image/webp" :auto-upload="false" :show-file-list="false" :on-change="changeAvatar"><el-button>选择图片</el-button></el-upload>
              <el-button v-if="profileForm.avatarData" text type="danger" @click="profileForm.avatarData=''">移除头像</el-button>
              <small>支持 PNG、JPG、WebP，原图不超过 5 MB</small>
            </div>
          </div>
        </el-form-item>
        <div class="profile-grid">
          <el-form-item label="登录工号"><el-input :model-value="userStore.user?.employeeNo" disabled /></el-form-item>
          <el-form-item label="员工姓名"><el-input v-model="profileForm.name" disabled /></el-form-item>
          <el-form-item label="已分配角色"><el-input :model-value="profileRoleText" disabled /></el-form-item>
          <el-form-item class="profile-full" label="授权范围"><el-input :model-value="profileScopeText" type="textarea" :rows="2" resize="none" disabled /></el-form-item>
          <el-form-item label="手机号码"><el-input v-model="profileForm.phone" maxlength="20" /></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="profileForm.email" maxlength="100" /></el-form-item>
        </div>
        <el-divider content-position="left">修改密码（选填）</el-divider>
        <div class="profile-grid password-grid">
          <el-form-item label="当前密码"><el-input v-model="profileForm.currentPassword" type="password" show-password autocomplete="current-password" /></el-form-item>
          <el-form-item label="新密码"><el-input v-model="profileForm.newPassword" type="password" show-password autocomplete="new-password" /></el-form-item>
          <el-form-item label="确认新密码"><el-input v-model="profileForm.confirmPassword" type="password" show-password autocomplete="new-password" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="profileOpen=false">取消</el-button><el-button type="primary" :loading="profileSaving" @click="saveProfile">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.shell { min-height: 100vh; display: flex; }
.sidebar { width: 238px; position: fixed; inset: 0 auto 0 0; z-index: 10; display: flex; flex-direction: column; color: #eaf5f1; background: linear-gradient(180deg, #064d39 0%, #013f30 100%); transition: width .2s; }
.sidebar.collapsed { width: 72px; }
.brand { height: 88px; display: flex; align-items: center; gap: 12px; padding: 0 20px; border-bottom: 1px solid rgba(255,255,255,.09); overflow: hidden; white-space: nowrap; }
.brand-mark { width: 54px; height: 54px; flex: 0 0 54px; display: grid; place-items: center; overflow: hidden; border-radius: 0; background: transparent; font-weight: 800; color: #103d31; }
.brand-mark img { display: block; width: 100%; height: 100%; object-fit: contain; filter: grayscale(1) contrast(8); mix-blend-mode: screen; }
.brand strong, .brand span { display: block; }.brand strong { font-size: 20px; letter-spacing: 0; }.brand span { margin-top: 4px; color: #dcebe4; font-size: 13px; letter-spacing: 0; }
.nav { flex: 1; padding: 16px 10px; border: 0; background: transparent; }
.nav :deep(.el-menu-item) { position: relative; height: 48px; margin-bottom: 5px; border-radius: 10px; color: #bad0c9; }
.nav :deep(.el-menu-item:hover) { background: rgba(255,255,255,.08); color: white; }
.nav :deep(.el-menu-item.is-active) { color: white; background: var(--accent); }
.menu-alert-count{position:absolute;right:16px;top:50%;width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;margin:0;padding:0;border-radius:50%;color:#263127;background:#f2b21b;font-size:12px;font-weight:700;line-height:1;transform:translateY(-50%)}
.sidebar.collapsed .brand{justify-content:center;padding:0}.sidebar.collapsed .nav{width:100%;padding:12px 9px;overflow:visible}.sidebar.collapsed .nav :deep(.el-menu-item){width:44px;min-width:44px;height:44px;justify-content:center;margin:0 auto 4px;padding:0!important;overflow:visible}.sidebar.collapsed .nav :deep(.el-menu-item .el-icon){margin:0}.sidebar.collapsed .menu-alert-count{top:-5px;right:-10px;width:20px;height:20px;color:#fff;background:#f2a900;font-size:11px;transform:none;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,40,29,.22)}
.collapse-btn { height: 56px; border: 0; border-top: 1px solid rgba(255,255,255,.09); background: transparent; color: #a9c2ba; display: flex; align-items: center; gap: 12px; padding: 0 26px; cursor: pointer; white-space: nowrap; }
.workspace { min-width: 0; flex: 1; margin-left: 238px; transition: margin .2s; }.sidebar.collapsed + .workspace { margin-left: 72px; }
.topbar { height: 83px; padding: 0 34px; display: flex; justify-content: space-between; align-items: center; background: rgba(250,249,232,.64); border-bottom: 1px solid var(--line); color: #16231d; position: sticky; top: 0; z-index: 5; backdrop-filter: blur(10px); }.farm-context{display:flex;align-items:center;gap:10px;color:#18251f;font-size:16px;font-weight:700}.farm-context-icon{color:#111;font-size:22px}.farm-context-select{width:168px}.farm-context-select :deep(.el-select__wrapper){min-height:34px;padding:0;border:0;background:transparent;box-shadow:none!important}.farm-context-select :deep(.el-select__selected-item){color:inherit;font-size:inherit;font-weight:inherit}
.topbar.context-hidden { justify-content: flex-end; }
.farm-dot { width: 8px; height: 8px; display: inline-block; margin-right: 7px; border-radius: 50%; background: #39ae75; box-shadow: 0 0 0 4px #dff4e9; }.online { display:none;margin-left: 10px; padding: 4px 8px; border-radius: 9px; font-size: 12px; }.online.success{color:#2a875f;background:#e9f7f0}.online.info{color:#267f99;background:#e7f5f8}.online.warning{color:#a46823;background:#fff3df}.online.danger{color:#b84d4d;background:#fdecec}
.user-area { display: flex; align-items: center; gap: 14px; }.profile-trigger{display:flex;align-items:center;gap:10px;padding:3px;border:0;border-radius:9px;color:inherit;background:transparent;font:inherit;cursor:pointer}.profile-trigger:hover{color:var(--accent);background:rgba(35,122,67,.06)}.avatar { width: 45px; height: 45px; display: grid; place-items: center; overflow:hidden; border-radius: 50%; color: white; background: #d4a43d; font-size:17px; font-weight:700; }.avatar img,.avatar-preview img{width:100%;height:100%;display:block;object-fit:cover}.avatar-editor{display:flex;align-items:center;gap:18px}.avatar-preview{width:72px;height:72px;display:grid;place-items:center;flex:0 0 72px;overflow:hidden;border-radius:50%;color:#fff;background:var(--accent);font-size:25px;font-weight:700}.avatar-actions{display:flex;align-items:center;gap:4px;flex-wrap:wrap}.avatar-actions small{width:100%;margin-top:4px;color:#8a9893;font-size:11px}
.profile-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}.profile-grid .profile-full{grid-column:1/-1}.password-grid{grid-template-columns:repeat(3,1fr)}
.notification-btn{width:36px;height:36px;display:grid;place-items:center;border:0;border-radius:50%;color:#17231e;background:transparent;cursor:pointer;font-size:22px}.notification-btn:hover{color:var(--accent);background:rgba(35,122,67,.06)}
.notification-badge :deep(.el-badge__content){border-color:#faf9e8;color:#fff;background:#f2b21b;font-weight:700}
.font-trigger{width:42px;height:42px;display:flex;align-items:baseline;justify-content:center;gap:2px;border:1px solid var(--line);border-radius:10px;color:#426458;background:#f8fbf9;cursor:pointer;transition:.2s}.font-trigger:hover{border-color:var(--accent);color:var(--accent);background:#f0f8f4}.font-trigger span{font-size:18px;font-weight:700}.font-trigger .font-small{font-size:11px;font-weight:600}.font-control{padding:2px}.font-control-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.font-control-head strong,.font-control-head small{display:block}.font-control-head strong{color:#29473d;font-size:14px}.font-control-head small{margin-top:4px;color:#8a9893;font-size:11px}.font-slider{display:grid;grid-template-columns:18px 1fr 18px;align-items:center;gap:10px;margin:18px 2px 14px;color:#70847b;font-size:11px}.font-preview{position:relative;padding:12px 13px;border:1px solid #e2eee8;border-radius:11px;background:#f5faf7}.font-preview span{color:#85a096;font-size:10px}.font-preview p{margin:5px 0 0;color:#315347;font-size:var(--app-font-size);font-weight:600}.font-preview em{position:absolute;right:10px;top:10px;color:#5c927a;font-size:10px;font-style:normal}
.role-switch { display: flex; align-items: center; gap: 6px; padding: 7px 11px; border: 1px solid var(--line); border-radius: 9px; color: #385249; background: #f8fbf9; cursor: pointer; }.role-switch:hover { border-color: var(--accent); color: var(--accent); }.single-role { padding: 6px 9px; border-radius: 8px; color: var(--accent); background: #f0f6f3; font-size: 13px; font-weight:700; }.display-name{color:#15241d;font-size:16px;font-weight:700}.user-area>.el-button{color:#293d34;font-size:15px}.current-role { color: var(--accent); font-weight: 600; }
.sidebar-mascot{width:100%;min-height:86px;display:flex;align-items:center;justify-content:center;gap:10px;padding:8px 14px;border:0;color:#dbece5;background:transparent;cursor:pointer;text-align:left;transition:.2s}.sidebar-mascot:hover,.sidebar-mascot.active{background:rgba(255,255,255,.1)}.sidebar-mascot.collapsed{min-height:76px;padding:7px 0}.sidebar-mascot-copy{display:flex;flex-direction:column;min-width:0}.sidebar-mascot-copy strong{color:#fff;font-size:13px}.sidebar-mascot-copy small{margin-top:3px;color:#b9d5c9;font-size:10px}.sidebar-orange{position:relative;display:block;width:58px;height:58px;flex:0 0 58px;border-radius:48% 52% 50% 50%;background:#f0a43b;box-shadow:inset -6px -8px 0 rgba(139,77,24,.12),0 8px 16px rgba(4,34,24,.18);transition:.22s}.sidebar-mascot:hover .sidebar-orange{transform:translateY(-2px) rotate(-1deg)}.sidebar-orange .leaf{position:absolute;right:4px;top:-7px;width:22px;height:10px;border:1px solid #396c4b;border-radius:100% 0 100% 0;background:#71a85b;transform:rotate(-23deg)}.sidebar-orange .eye{position:absolute;top:22px;width:6px;height:9px;border-radius:50%;background:#543c2d}.sidebar-orange .eye-left{left:17px}.sidebar-orange .eye-right{right:17px}.sidebar-orange .mouth{position:absolute;left:23px;top:35px;width:13px;height:8px;border-bottom:2px solid #543c2d;border-radius:0 0 50% 50%}.sidebar-orange .cheek{position:absolute;top:35px;width:8px;height:5px;border-radius:50%;background:rgba(181,65,47,.28)}.sidebar-orange .cheek-left{left:9px}.sidebar-orange .cheek-right{right:9px}.sidebar-mascot.active .sidebar-orange{animation:mascot-breathe 1.7s ease-in-out infinite}@keyframes mascot-breathe{50%{transform:translateY(-3px) rotate(1deg)}}
.content { padding: 28px; }
@media (max-width: 900px) { .sidebar { width: 72px; }.sidebar .brand > div:last-child, .collapse-btn span, .nav :deep(.el-menu-item span:not(.menu-alert-count)), .sidebar-mascot-copy { display: none; }.brand{height:82px;padding:0;justify-content:center}.brand-mark{width:48px;height:48px;flex-basis:48px}.nav :deep(.el-menu-item) { justify-content: center; padding: 0 !important; }.menu-alert-count{top:5px;right:5px;width:17px;height:17px;font-size:9px;transform:none}.sidebar-mascot{padding:7px 0}.workspace { margin-left: 72px; }.topbar { height:64px;padding: 0 18px; }.topbar > div:first-child, .display-name { display:none; }.content { padding: 18px; } }
@media (max-width: 620px) { .profile-grid,.password-grid{grid-template-columns:1fr}.profile-grid .profile-full{grid-column:auto} }
</style>
