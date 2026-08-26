<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const form = reactive({ username: '', password: '', remember: true })

async function submit() {
  if (!form.username.trim() || !form.password) return ElMessage.warning('请输入用户名和密码')
  loading.value = true
  try {
    const home = await userStore.login(form)
    await router.replace(home)
    ElMessage.success('登录成功')
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error.message || '登录失败，请稍后重试')
  } finally { loading.value = false }
}
</script>

<template>
  <div class="login-page">
    <section class="intro">
      <div class="intro-inner">
        <div class="brand-mark">禾</div>
        <p class="eyebrow">SMART AGRICULTURE</p>
        <h1>让每一滴水<br><span>灌溉得恰到好处</span></h1>
        <p class="lead">融合环境监测、天气预报与智慧决策，帮助农场实现精细化、可持续管理。</p>
        <div class="feature-row"><span>实时感知</span><span>天气联动</span><span>智能决策</span></div>
      </div>
      <div class="field-art"><i></i><i></i><i></i><i></i></div>
    </section>

    <section class="login-panel">
      <form class="login-card" @submit.prevent="submit">
        <div class="mobile-logo">禾</div>
        <p class="eyebrow panel-eyebrow">WELCOME BACK</p>
        <h2>欢迎回来</h2>
        <p class="hint">使用账号密码登录，系统会自动加载该账号拥有的角色和管理权限。</p>

        <label for="username">用户名</label>
        <el-input id="username" v-model="form.username" size="large" placeholder="请输入用户名" :prefix-icon="User" />
        <label for="password">密码</label>
        <el-input id="password" v-model="form.password" size="large" type="password" show-password placeholder="请输入密码" :prefix-icon="Lock" @keyup.enter="submit" />
        <div class="form-meta"><el-checkbox v-model="form.remember">记住我</el-checkbox><button type="button" @click="ElMessage.info('请联系系统管理员重置密码')">忘记密码？</button></div>
        <el-button class="submit" size="large" native-type="submit" :loading="loading">登录平台</el-button>

        <div class="register-entry">
          <span>还没有账号？</span><button type="button" @click="router.push('/register')">立即注册</button>
          <small>仅开放农户与农场管理员注册</small>
        </div>
        <p class="demo-note">演示账号：zhangsan / 123456（拥有三个角色）</p>
      </form>
    </section>
  </div>
</template>

<style scoped>
.login-page{min-height:100vh;display:grid;grid-template-columns:48% 52%;background:#f7faf8}.intro{position:relative;overflow:hidden;color:#fff;background:radial-gradient(circle at 30% 22%,rgba(78,179,124,.52),transparent 31%),linear-gradient(145deg,#153f33,#092b23)}.intro::before{position:absolute;inset:0;content:'';opacity:.09;background-image:linear-gradient(30deg,transparent 48%,#fff 49%,transparent 51%);background-size:38px 38px}.intro-inner{position:relative;z-index:2;max-width:570px;margin:0 auto;padding:13vh 62px}.brand-mark,.mobile-logo{width:54px;height:54px;display:grid;place-items:center;border-radius:16px;color:#113c31;background:#63ca94;box-shadow:0 10px 24px #081f1a55;font-size:21px;font-weight:800}.eyebrow{margin:23px 0 0;color:#9dd7ba;font-size:11px;font-weight:700;letter-spacing:3px}.intro h1{margin:28px 0 22px;font-size:clamp(40px,4vw,62px);line-height:1.15;letter-spacing:-2px}.intro h1 span{color:#78d7a5}.lead{max-width:470px;color:#b7d2c9;line-height:1.9}.feature-row{display:flex;gap:12px;margin-top:38px}.feature-row span{padding:8px 13px;border:1px solid #ffffff22;border-radius:20px;color:#d2e6df;background:#ffffff0c;font-size:12px}.field-art{position:absolute;right:-6%;bottom:-16%;left:-12%;height:40%;opacity:.18;transform:rotate(-5deg)}.field-art i{position:absolute;bottom:0;width:2px;height:120%;border-radius:50%;background:linear-gradient(transparent,#91d7b1);transform-origin:bottom}.field-art i:nth-child(1){left:24%;transform:rotate(-20deg)}.field-art i:nth-child(2){left:39%;height:95%;transform:rotate(-8deg)}.field-art i:nth-child(3){left:61%;height:110%;transform:rotate(12deg)}.field-art i:nth-child(4){left:78%;height:85%;transform:rotate(24deg)}.login-panel{display:grid;place-items:center;padding:42px}.login-card{width:min(520px,100%);padding:36px 42px;border:1px solid #e0ebe5;border-radius:24px;background:rgba(255,255,255,.92);box-shadow:0 20px 55px rgba(18,63,48,.09)}.mobile-logo{display:none}.panel-eyebrow{margin:0 0 7px;color:#2b8a63}.login-card h2{margin:0 0 8px;color:#193b30;font-size:31px}.hint{margin:0 0 25px;color:#788780;font-size:13px}.login-card>label{display:block;margin:18px 0 8px;color:#385249;font-size:13px;font-weight:650}.form-meta{display:flex;justify-content:space-between;align-items:center;margin:16px 0;color:#87968f;font-size:12px}.form-meta button,.register-entry button{border:0;color:#287e5b;background:transparent;cursor:pointer}.submit{width:100%;height:44px;border:0;color:#fff;background:linear-gradient(100deg,#2d9468,#176748);box-shadow:0 9px 20px rgba(36,126,88,.2)}.submit:hover{color:#fff;background:linear-gradient(100deg,#26875f,#125c40)}.register-entry{display:flex;align-items:center;justify-content:center;gap:4px;margin-top:23px;padding-top:20px;border-top:1px solid #edf2ef;color:#7b8b84;font-size:13px}.register-entry button{font-weight:700}.register-entry small{display:block;margin-left:7px;padding:4px 7px;border-radius:8px;color:#71877d;background:#eff6f2;font-size:9px}.demo-note{display:none}.mobile-logo{margin-bottom:20px}@media(max-width:900px){.login-page{grid-template-columns:1fr}.intro{display:none}.login-panel{min-height:100vh;padding:22px}.login-card{padding:30px 25px}.mobile-logo{display:grid}.login-card h2{font-size:27px}}@media(max-width:470px){.register-entry{flex-wrap:wrap}.register-entry small{width:100%;margin:4px 0 0;text-align:center}}
</style>
