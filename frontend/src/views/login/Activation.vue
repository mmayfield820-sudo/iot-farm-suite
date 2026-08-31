<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Key, Lock, Phone, User } from '@element-plus/icons-vue'
import { completeActivation, verifyActivation } from '@/api/adminPhase2'

const router = useRouter()
const step = ref(1)
const verifying = ref(false)
const submitting = ref(false)
const info = ref(null)
const verifyForm = reactive({ identifier: '', activationCode: '' })
const completeForm = reactive({ username: '', password: '', confirmPassword: '', phone: '', email: '' })
const roleLabels = { farmer: '农户', farm_admin: '农场管理员', system_admin: '系统管理员' }
const roleText = computed(() => (info.value?.roles || []).map((role) => roleLabels[role] || role).join('、') || '暂未分配')
const scopes = computed(() => [
  ...(info.value?.farmScopes || []).map((item) => ({ ...item, type: '授权农场' })),
  ...(info.value?.plotScopes || []).map((item) => ({ ...item, type: '授权地块' })),
])

async function verify() {
  if (!verifyForm.identifier.trim() || !verifyForm.activationCode.trim()) return ElMessage.warning('请输入工号或手机号以及激活凭证')
  verifying.value = true
  try {
    info.value = await verifyActivation({ identifier: verifyForm.identifier.trim(), activationCode: verifyForm.activationCode.trim() })
    Object.assign(completeForm, { username: '', password: '', confirmPassword: '', phone: info.value.phone || '', email: info.value.email || '' })
    step.value = 2
  } catch (error) { ElMessage.error(error?.response?.data?.message || error.message || '身份验证失败') }
  finally { verifying.value = false }
}

async function complete() {
  if (!/^[A-Za-z0-9_]{4,50}$/.test(completeForm.username)) return ElMessage.warning('用户名需为 4—50 位字母、数字或下划线')
  if (completeForm.password.length < 8) return ElMessage.warning('密码至少需要 8 位')
  if (completeForm.password !== completeForm.confirmPassword) return ElMessage.warning('两次输入的密码不一致')
  if (!/^1\d{10}$/.test(completeForm.phone)) return ElMessage.warning('请输入正确的 11 位手机号')
  if (completeForm.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(completeForm.email)) return ElMessage.warning('请输入正确的邮箱地址')
  submitting.value = true
  try {
    await completeActivation({ verificationToken: info.value.verificationToken, username: completeForm.username, password: completeForm.password, phone: completeForm.phone, email: completeForm.email || null })
    ElMessage.success('账号激活成功，请使用新凭证登录')
    router.replace('/login')
  } catch (error) { ElMessage.error(error?.response?.data?.message || error.message || '账号激活失败') }
  finally { submitting.value = false }
}
</script>

<template>
  <div class="activation-page">
    <header class="auth-header"><button class="brand" type="button" @click="router.push('/login')"><span>橙</span><strong>橙心如意</strong></button><button class="back" type="button" @click="router.push('/login')"><el-icon><ArrowLeft /></el-icon> 返回登录</button></header>
    <main class="activation-shell">
      <section class="activation-intro"><p>EMPLOYEE ACTIVATION</p><h1>激活预置员工账号</h1><span>账号、角色和管理范围均由管理员预先分配。完成身份验证后，你只需设置自己的登录凭证并确认联系方式。</span><div class="steps"><i :class="{ active: step >= 1 }">1</i><b></b><i :class="{ active: step >= 2 }">2</i></div><div class="step-labels"><span>验证员工身份</span><span>设置登录凭证</span></div></section>

      <section v-if="step === 1" class="activation-card">
        <div class="card-heading"><span><User /></span><div><h2>验证员工身份</h2><p>输入管理员提供的激活信息，验证结果 15 分钟内有效。</p></div></div>
        <label>工号或手机号</label><el-input v-model="verifyForm.identifier" size="large" maxlength="50" placeholder="请输入工号或预留手机号" :prefix-icon="Phone" @keyup.enter="verify" />
        <label>激活凭证</label><el-input v-model="verifyForm.activationCode" size="large" type="password" show-password placeholder="请输入管理员单独提供的激活凭证" :prefix-icon="Key" @keyup.enter="verify" />
        <el-alert title="没有员工档案或激活凭证？请联系系统管理员导入员工信息或重置凭证。" type="info" :closable="false" show-icon />
        <el-button class="primary-action" type="primary" size="large" :loading="verifying" @click="verify">验证并继续</el-button>
      </section>

      <section v-else class="activation-card wide-card">
        <div class="card-heading"><span><Lock /></span><div><h2>设置登录凭证</h2><p>请确认管理员预置的信息，并设置今后用于登录平台的凭证。</p></div></div>
        <div class="readonly-grid"><div><small>员工姓名</small><strong>{{ info.name }}</strong></div><div><small>员工工号</small><strong>{{ info.employeeNo }}</strong></div><div><small>已分配角色</small><strong>{{ roleText }}</strong></div><div><small>授权范围</small><strong>{{ scopes.length ? `${scopes.length} 项` : '无' }}</strong></div></div>
        <div v-if="scopes.length" class="scope-list"><span v-for="item in scopes" :key="`${item.type}-${item.id}`"><small>{{ item.type }}</small><strong>{{ item.name }}</strong><em>{{ item.id }}</em></span></div>
        <p class="readonly-note">以上角色和授权范围由管理员分配，仅供核对，员工无法自行修改。</p>
        <div class="form-grid">
          <label><span>登录用户名</span><el-input v-model="completeForm.username" size="large" maxlength="50" placeholder="4—50 位字母、数字或下划线" /></label>
          <label><span>手机号</span><el-input v-model="completeForm.phone" size="large" maxlength="11" placeholder="确认用于联系的手机号" /></label>
          <label><span>登录密码</span><el-input v-model="completeForm.password" size="large" type="password" show-password placeholder="至少 8 位" /></label>
          <label><span>确认密码</span><el-input v-model="completeForm.confirmPassword" size="large" type="password" show-password placeholder="再次输入密码" /></label>
          <label class="full"><span>邮箱（选填）</span><el-input v-model="completeForm.email" size="large" placeholder="用于接收通知和找回密码" /></label>
        </div>
        <div class="actions"><el-button size="large" @click="step = 1">重新验证</el-button><el-button type="primary" size="large" :loading="submitting" @click="complete">完成激活</el-button></div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.activation-page{min-height:100vh;padding:0 28px 45px;color:#4a2b1b;background:radial-gradient(circle at 15% 8%,rgba(239,139,47,.2),transparent 29%),linear-gradient(145deg,#fff6eb,#fffdfa 52%,#fff1df)}.auth-header{height:74px;max-width:1080px;display:flex;align-items:center;justify-content:space-between;margin:auto}.brand,.back{display:flex;align-items:center;gap:10px;border:0;color:#633a22;background:transparent;cursor:pointer}.brand span{width:40px;height:40px;display:grid;place-items:center;border-radius:12px;color:#4a2816;background:linear-gradient(145deg,#ffae4a,#ed7b1e);font-weight:800}.brand strong{font-size:17px}.back{color:#9b7359}.activation-shell{width:min(900px,100%);margin:24px auto}.activation-intro{text-align:center}.activation-intro>p{margin:0;color:#d06a20;font-size:10px;font-weight:800;letter-spacing:2.6px}.activation-intro h1{margin:10px 0 9px;font-size:32px}.activation-intro>span{display:block;max-width:640px;margin:auto;color:#8b7465;font-size:13px;line-height:1.7}.steps{width:260px;display:flex;align-items:center;margin:25px auto 6px}.steps i{width:30px;height:30px;display:grid;place-items:center;flex:0 0 30px;border:2px solid #e7cbb4;border-radius:50%;color:#b79984;background:#fff;font-style:normal;font-weight:700}.steps i.active{border-color:#df741b;color:#fff;background:#df741b}.steps b{height:2px;flex:1;background:#ebd4c2}.step-labels{width:330px;display:flex;justify-content:space-between;margin:auto;color:#9b7d69;font-size:11px}.activation-card{width:min(540px,100%);margin:24px auto 0;padding:32px 36px;border:1px solid #ecd8c7;border-radius:22px;background:rgba(255,253,250,.94);box-shadow:0 20px 55px rgba(108,55,20,.1)}.wide-card{width:min(780px,100%)}.card-heading{display:flex;align-items:center;gap:13px;margin-bottom:22px}.card-heading>span{width:46px;height:46px;display:grid;place-items:center;flex:0 0 46px;border-radius:14px;color:#c75d17;background:#fff0df;font-size:22px}.card-heading h2{margin:0;font-size:23px}.card-heading p{margin:5px 0 0;color:#907768;font-size:12px}.activation-card>label,.form-grid label>span{display:block;margin:17px 0 8px;color:#684731;font-size:13px;font-weight:650}.activation-card .el-alert{margin:20px 0}.primary-action{width:100%;height:44px;border:0;background:linear-gradient(100deg,#ed852a,#c65b14)}.readonly-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.readonly-grid>div{padding:13px;border-radius:12px;background:#fff5e9}.readonly-grid small,.readonly-grid strong{display:block}.readonly-grid small{color:#a18470;font-size:10px}.readonly-grid strong{margin-top:5px;font-size:13px}.scope-list{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:10px}.scope-list span{display:grid;grid-template-columns:70px 1fr auto;align-items:center;gap:8px;padding:10px 12px;border:1px solid #f0dfd1;border-radius:10px}.scope-list small,.scope-list em{color:#a08472;font-size:10px;font-style:normal}.scope-list strong{font-size:12px}.readonly-note{margin:12px 0 3px;padding:9px 11px;border-radius:9px;color:#947865;background:#fff8f1;font-size:10px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 18px}.form-grid .full{grid-column:1/-1}.actions{display:flex;justify-content:flex-end;gap:10px;margin-top:22px;padding-top:18px;border-top:1px solid #f0e5dc}.actions .el-button{min-width:130px}@media(max-width:680px){.activation-page{padding:0 16px 30px}.auth-header{height:64px}.activation-shell{margin-top:12px}.activation-card{padding:25px 20px}.readonly-grid,.form-grid,.scope-list{grid-template-columns:1fr}.form-grid .full{grid-column:auto}.activation-intro h1{font-size:26px}.scope-list span{grid-template-columns:65px 1fr auto}}
</style>
