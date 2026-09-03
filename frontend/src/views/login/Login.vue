<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { ROLE_LABEL, useUserStore } from '@/stores/user'
import { completeFirstLogin } from '@/api/auth'
import farmBrandLogo from '@/assets/farm-brand-logo.png'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const setupLoading = ref(false)
const setupToken = ref('')
const setupProfile = ref(null)
const form = reactive({ employeeNo: '', password: '', remember: true })
const setupForm = reactive({ password: '', confirmPassword: '', phone: '', email: '' })
const introVisible = ref(true)
const introLeaving = ref(false)
const videoRef = ref(null)
let introTimer
const setupRoleText = computed(() => (setupProfile.value?.roles || []).map((role) => ROLE_LABEL[role] || role).join('、') || '暂未分配')
const setupScopes = computed(() => [
  ...(setupProfile.value?.farmScopes || []).map((item) => ({ ...item, type: '授权农场' })),
  ...(setupProfile.value?.plotScopes || []).map((item) => ({ ...item, type: '授权地块' })),
])

function finishIntro() {
  if (!introVisible.value || introLeaving.value) return
  introLeaving.value = true
  window.clearTimeout(introTimer)
  introTimer = window.setTimeout(() => {
    introVisible.value = false
    introLeaving.value = false
  }, 720)
}

onMounted(async () => {
  try { await videoRef.value?.play() } catch { finishIntro() }
})
onBeforeUnmount(() => window.clearTimeout(introTimer))

async function submit() {
  if (!form.employeeNo.trim() || !form.password) return ElMessage.warning('请输入工号和密码')
  loading.value = true
  try {
    const result = await userStore.login(form)
    if (result.requiresProfileCompletion) {
      setupToken.value = result.profileSetupToken
      setupProfile.value = result.setupProfile
      setupForm.phone = result.setupProfile?.phone || ''
      setupForm.email = result.setupProfile?.email || ''
      return
    }
    await router.replace(result.home)
    ElMessage.success('登录成功')
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error.message || '登录失败，请稍后重试')
  } finally { loading.value = false }
}

function cancelSetup() {
  setupToken.value = ''
  setupProfile.value = null
  form.password = ''
  Object.assign(setupForm, { password: '', confirmPassword: '', phone: '', email: '' })
}

async function submitSetup() {
  if (setupForm.password.length < 6) return ElMessage.warning('请设置至少 6 位的新密码')
  if (setupForm.password !== setupForm.confirmPassword) return ElMessage.warning('两次输入的密码不一致')
  setupLoading.value = true
  try {
    await completeFirstLogin({ profileSetupToken: setupToken.value, password: setupForm.password, phone: setupForm.phone || null, email: setupForm.email || null })
    form.password = setupForm.password
    const result = await userStore.login(form)
    await router.replace(result.home)
    ElMessage.success('账号已启用')
  } catch (error) {
    ElMessage.error(error?.message || '账号启用失败')
  } finally { setupLoading.value = false }
}
</script>

<template>
  <div class="login-page">
    <div v-if="introVisible && !setupToken" class="intro-screen" :class="{ leaving: introLeaving }">
      <video ref="videoRef" class="intro-video" muted autoplay playsinline preload="auto" @ended="finishIntro" @error="finishIntro">
        <source src="/orchard-intro.mp4" type="video/mp4" />
      </video>
      <button class="skip-intro" type="button" @click="finishIntro">跳过动画</button>
    </div>
    <section v-if="setupToken" class="activation-page">
      <header class="activation-header">
        <div class="activation-brand"><span><img :src="farmBrandLogo" alt="" /></span><strong>橙心如意</strong></div>
        <button type="button" @click="cancelSetup">返回登录</button>
      </header>
      <main class="activation-shell">
        <div class="activation-heading"><p>员工账号激活</p><h1>激活预置员工账号</h1><span>账号、角色和管理范围由管理员预先分配。请核对员工信息，并设置正式登录密码和联系方式。</span></div>
        <div class="activation-steps"><div class="done"><i>1</i><span>验证员工身份</span></div><b></b><div class="active"><i>2</i><span>设置登录凭证</span></div></div>
        <form class="activation-card" @submit.prevent="submitSetup">
          <div class="activation-card-title"><span><Lock /></span><div><h2>设置登录凭证</h2><p>请确认管理员预置的信息，并设置今后用于登录平台的凭证。</p></div></div>
          <div class="profile-summary">
            <div><small>员工姓名</small><strong>{{ setupProfile?.displayName || '-' }}</strong></div>
            <div><small>员工工号</small><strong>{{ setupProfile?.employeeNo }}</strong></div>
            <div><small>已分配角色</small><strong>{{ setupRoleText }}</strong></div>
            <div><small>授权范围</small><strong>{{ setupScopes.length }} 项</strong></div>
          </div>
          <div v-if="setupScopes.length" class="scope-list"><span v-for="item in setupScopes" :key="`${item.type}-${item.id}`"><small>{{ item.type }}</small><strong>{{ item.name || item.id }}</strong><em>{{ item.id }}</em></span></div>
          <p class="readonly-note">以上员工档案、角色和授权范围由管理员分配，仅供核对，员工无法自行修改。</p>
          <div class="activation-form-grid">
            <label><span>登录工号</span><el-input :model-value="setupProfile?.employeeNo" size="large" disabled /></label>
            <label><span>手机号</span><el-input v-model="setupForm.phone" size="large" maxlength="20" placeholder="请输入手机号" :prefix-icon="User" /></label>
            <label><span>登录密码</span><el-input v-model="setupForm.password" size="large" type="password" show-password placeholder="至少 6 位" :prefix-icon="Lock" /></label>
            <label><span>确认密码</span><el-input v-model="setupForm.confirmPassword" size="large" type="password" show-password placeholder="再次输入登录密码" :prefix-icon="Lock" /></label>
            <label class="full"><span>邮箱（选填）</span><el-input v-model="setupForm.email" size="large" maxlength="100" placeholder="请输入邮箱" :prefix-icon="User" /></label>
          </div>
          <div class="activation-actions"><el-button size="large" @click="cancelSetup">重新验证</el-button><el-button class="activation-submit" size="large" native-type="submit" :loading="setupLoading">完成激活</el-button></div>
        </form>
      </main>
    </section>
    <section v-else class="intro">
      <div class="intro-inner">
        <div class="brand-mark"><img :src="farmBrandLogo" alt="" /></div>
        <p class="eyebrow">奉节脐橙智慧农业</p>
        <h1>橙心守护每一园<br><span>如意管理每一程</span></h1>
        <p class="lead">面向奉节脐橙产区，融合环境监测、智慧灌溉与辅助决策，让橙园管理更清晰、更从容。</p>
        <div class="feature-row"><span>橙园总览</span><span>土壤湿度监测</span><span>智慧灌溉</span></div>
      </div>
      <div class="field-art"><i></i><i></i><i></i><i></i></div>
    </section>

    <section v-if="!setupToken" class="login-panel">
      <form class="login-card" @submit.prevent="submit">
        <div class="mobile-logo"><img :src="farmBrandLogo" alt="" /></div>
        <p class="eyebrow panel-eyebrow">WELCOME BACK</p>
        <h2>欢迎回来</h2>
        <p class="hint">使用账号密码登录，系统会自动加载该账号拥有的角色和管理权限。</p>

        <label for="employee-no">员工工号</label>
        <el-input id="employee-no" v-model="form.employeeNo" size="large" placeholder="请输入员工工号" :prefix-icon="User" />
        <label for="password">密码</label>
        <el-input id="password" v-model="form.password" size="large" type="password" show-password placeholder="请输入密码" :prefix-icon="Lock" @keyup.enter="submit" />
        <div class="form-meta"><el-checkbox v-model="form.remember">记住我</el-checkbox><button type="button" @click="ElMessage.info('请联系系统管理员重置密码')">忘记密码？</button></div>
        <el-button class="submit" size="large" native-type="submit" :loading="loading">登录平台</el-button>

        <div class="first-login-entry"><span>首次使用平台？</span><strong>使用工号和身份证后六位登录</strong><small>无需激活码</small></div>
      </form>
    </section>
  </div>
</template>

<style scoped>
.login-page{min-height:100vh;display:grid;grid-template-columns:48% 52%;background:#f7faf8}.intro{position:relative;overflow:hidden;color:#fff;background:radial-gradient(circle at 30% 22%,rgba(78,179,124,.52),transparent 31%),linear-gradient(145deg,#153f33,#092b23)}.intro::before{position:absolute;inset:0;content:'';opacity:.09;background-image:linear-gradient(30deg,transparent 48%,#fff 49%,transparent 51%);background-size:38px 38px}.intro-inner{position:relative;z-index:2;max-width:570px;margin:0 auto;padding:13vh 62px}.brand-mark,.mobile-logo{width:54px;height:54px;display:grid;place-items:center;border-radius:16px;color:#113c31;background:#63ca94;box-shadow:0 10px 24px #081f1a55;font-size:21px;font-weight:800}.eyebrow{margin:23px 0 0;color:#9dd7ba;font-size:11px;font-weight:700;letter-spacing:3px}.intro h1{margin:28px 0 22px;font-size:clamp(40px,4vw,62px);line-height:1.15;letter-spacing:-2px}.intro h1 span{color:#78d7a5}.lead{max-width:470px;color:#b7d2c9;line-height:1.9}.feature-row{display:flex;gap:12px;margin-top:38px}.feature-row span{padding:8px 13px;border:1px solid #ffffff22;border-radius:20px;color:#d2e6df;background:#ffffff0c;font-size:12px}.field-art{position:absolute;right:-6%;bottom:-16%;left:-12%;height:40%;opacity:.18;transform:rotate(-5deg)}.field-art i{position:absolute;bottom:0;width:2px;height:120%;border-radius:50%;background:linear-gradient(transparent,#91d7b1);transform-origin:bottom}.field-art i:nth-child(1){left:24%;transform:rotate(-20deg)}.field-art i:nth-child(2){left:39%;height:95%;transform:rotate(-8deg)}.field-art i:nth-child(3){left:61%;height:110%;transform:rotate(12deg)}.field-art i:nth-child(4){left:78%;height:85%;transform:rotate(24deg)}.login-panel{display:grid;place-items:center;padding:42px}.login-card{width:min(520px,100%);padding:36px 42px;border:1px solid #e0ebe5;border-radius:24px;background:rgba(255,255,255,.92);box-shadow:0 20px 55px rgba(18,63,48,.09)}.mobile-logo{display:none}.panel-eyebrow{margin:0 0 7px;color:#2b8a63}.login-card h2{margin:0 0 8px;color:#193b30;font-size:31px}.hint{margin:0 0 25px;color:#788780;font-size:13px}.login-card>label{display:block;margin:18px 0 8px;color:#385249;font-size:13px;font-weight:650}.form-meta{display:flex;justify-content:space-between;align-items:center;margin:16px 0;color:#87968f;font-size:12px}.form-meta button,.first-login-entry button{border:0;color:#287e5b;background:transparent;cursor:pointer}.submit{width:100%;height:44px;border:0;color:#fff;background:linear-gradient(100deg,#2d9468,#176748);box-shadow:0 9px 20px rgba(36,126,88,.2)}.submit:hover{color:#fff;background:linear-gradient(100deg,#26875f,#125c40)}.first-login-entry{display:flex;align-items:center;justify-content:center;gap:4px;margin-top:23px;padding-top:20px;border-top:1px solid #edf2ef;color:#7b8b84;font-size:13px}.first-login-entry button{font-weight:700}.first-login-entry small{display:block;margin-left:7px;padding:4px 7px;border-radius:8px;color:#71877d;background:#eff6f2;font-size:9px}.demo-note{display:none}.mobile-logo{margin-bottom:20px}@media(max-width:900px){.login-page{grid-template-columns:1fr}.intro{display:none}.login-panel{min-height:100vh;padding:22px}.login-card{padding:30px 25px}.mobile-logo{display:grid}.login-card h2{font-size:27px}}@media(max-width:470px){.first-login-entry{flex-wrap:wrap}.first-login-entry small{width:100%;margin:4px 0 0;text-align:center}}
.intro-screen{position:fixed;inset:0;z-index:100;overflow:hidden;background:#153f33;transition:opacity .72s ease,visibility .72s ease}.intro-screen.leaving{opacity:0;visibility:hidden}.intro-video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.skip-intro{position:absolute;right:28px;top:25px;padding:8px 14px;border:1px solid rgba(255,255,255,.32);border-radius:999px;color:#fff;background:rgba(18,67,49,.3);font-size:12px;cursor:pointer;backdrop-filter:blur(8px)}.skip-intro:hover{background:rgba(255,255,255,.18)}@media(max-width:700px){.skip-intro{right:18px;top:18px}}
.login-page{background:#faf9e8}.intro{background:linear-gradient(145deg,#174b3c,#0c3027)}.brand-mark,.mobile-logo{width:58px;height:58px;overflow:hidden;border-radius:14px;background:#2c8a65}.brand-mark img,.mobile-logo img{width:100%;height:100%;display:block;object-fit:contain;filter:grayscale(1) contrast(8);mix-blend-mode:screen}.eyebrow,.intro h1{letter-spacing:0}.intro h1 span{color:#f2b21b}.lead{color:#c7ddd3}.feature-row span{color:#e1eee8}.login-panel{background:rgba(250,249,232,.78)}.login-card{border-color:#dce8df;background:rgba(255,255,255,.96);box-shadow:0 20px 55px rgba(18,63,48,.1)}.submit{background:#237a55}.submit:hover{background:#196947}.first-login-entry strong{color:#237a55}.first-login-entry small{color:#9a6716;background:#fff4cf}
.activation-page{grid-column:1/-1;min-height:100vh;padding:0 28px 48px;color:#24463a;background:#faf9e8}.activation-header{height:80px;max-width:1120px;display:flex;align-items:center;justify-content:space-between;margin:auto}.activation-brand{display:flex;align-items:center;gap:11px}.activation-brand span{width:48px;height:48px;display:grid;place-items:center;overflow:hidden;border-radius:13px;background:#247a58}.activation-brand img{width:100%;height:100%;object-fit:contain;filter:grayscale(1) contrast(8);mix-blend-mode:screen}.activation-brand strong{font-size:18px}.activation-header button{border:0;color:#607a70;background:transparent;font:inherit;cursor:pointer}.activation-header button::before{content:'‹';margin-right:8px;font-size:22px;vertical-align:-2px}.activation-shell{width:min(940px,100%);margin:25px auto 0}.activation-heading{text-align:center}.activation-heading>p{margin:0;color:#23815c;font-size:11px;font-weight:800;letter-spacing:0}.activation-heading h1{margin:10px 0 9px;color:#193b30;font-size:34px;letter-spacing:0}.activation-heading>span{display:block;max-width:700px;margin:auto;color:#74877f;font-size:13px;line-height:1.7}.activation-steps{width:340px;display:flex;align-items:flex-start;margin:26px auto 30px}.activation-steps>div{display:flex;flex-direction:column;align-items:center;gap:7px;color:#73877e;font-size:11px;white-space:nowrap}.activation-steps i{width:36px;height:36px;display:grid;place-items:center;border:2px solid #b9d6c8;border-radius:50%;color:#4f7d69;background:#fff;font-size:15px;font-style:normal;font-weight:700}.activation-steps .done i,.activation-steps .active i{border-color:#247a58;color:#fff;background:#247a58}.activation-steps b{height:2px;flex:1;margin-top:17px;background:#b9d6c8}.activation-card{padding:36px 42px;border:1px solid #d9e6df;border-radius:22px;background:#fff;box-shadow:0 20px 55px rgba(18,63,48,.1)}.activation-card-title{display:flex;align-items:center;gap:14px;margin-bottom:24px}.activation-card-title>span{width:50px;height:50px;display:grid;place-items:center;flex:0 0 50px;border-radius:14px;color:#b87511;background:#fff4cf;font-size:26px}.activation-card-title h2{margin:0;color:#193b30;font-size:25px}.activation-card-title p{margin:5px 0 0;color:#7b8c85;font-size:12px}.profile-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.profile-summary>div{padding:14px 16px;border-radius:12px;background:#f1f7f3}.profile-summary small,.profile-summary strong{display:block}.profile-summary small{color:#80938a;font-size:10px}.profile-summary strong{margin-top:6px;color:#284b3e;font-size:14px}.scope-list{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin-top:11px}.scope-list span{display:grid;grid-template-columns:72px 1fr auto;align-items:center;gap:9px;padding:11px 13px;border:1px solid #dce9e2;border-radius:10px}.scope-list small,.scope-list em{color:#84968e;font-size:10px;font-style:normal}.scope-list strong{font-size:12px}.readonly-note{margin:13px 0 22px;padding:10px 13px;border-radius:9px;color:#6e8379;background:#f6f8f5;font-size:11px}.activation-form-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px 22px}.activation-form-grid label>span{display:block;margin-bottom:8px;color:#385249;font-size:13px;font-weight:650}.activation-form-grid .full{grid-column:1/-1}.activation-actions{display:flex;justify-content:flex-end;gap:12px;margin-top:28px;padding-top:22px;border-top:1px solid #e8efeb}.activation-actions .el-button{min-width:150px}.activation-submit{border:0!important;color:#fff!important;background:#237a55!important}.activation-submit:hover{background:#196947!important}@media(max-width:700px){.activation-page{padding:0 16px 30px}.activation-header{height:68px}.activation-shell{margin-top:12px}.activation-heading h1{font-size:27px}.activation-steps{width:260px}.activation-card{padding:25px 20px}.profile-summary,.scope-list,.activation-form-grid{grid-template-columns:1fr}.activation-form-grid .full{grid-column:auto}.activation-actions .el-button{min-width:0;flex:1}}
</style>
