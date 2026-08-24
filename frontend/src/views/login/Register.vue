<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, CircleCheck, Collection, OfficeBuilding, UserFilled } from '@element-plus/icons-vue'
import { platformFarms, platformPlots } from '@/mock/platformData'
import { useRegistrationStore } from '@/stores/registration'
import { getFarmList } from '@/api/platform'
import { getPlotList } from '@/api/plot'
import { normalizeFarm, unwrapList } from '@/utils/dataAdapters'

const router = useRouter()
const registrationStore = useRegistrationStore()
const isMock = import.meta.env.VITE_USE_MOCK === 'true'
const availableFarms = ref(isMock ? platformFarms : [])
const availablePlots = ref(isMock ? platformPlots : [])
const step = ref(1)
const submitting = ref(false)
const keyword = ref('')
const form = reactive({
  username: '', realName: '', phone: '', email: '', password: '', confirmPassword: '',
  roles: ['farmer'], plotIds: [], farmIds: [], agreement: false,
})
const roleOptions = [
  { value: 'farmer', label: '农户', description: '申请查看和操作一个或多个授权地块', icon: UserFilled },
  { value: 'farmAdmin', label: '农场管理员', description: '申请管理一个或多个授权农场', icon: OfficeBuilding },
]
const steps = computed(() => [
  { value: 1, label: '填写资料' },
  ...(form.roles.includes('farmer') ? [{ value: 2, label: '选择农户地块' }] : []),
  ...(form.roles.includes('farmAdmin') ? [{ value: 3, label: '选择管理农场' }] : []),
  { value: 4, label: '提交成功' },
])
const currentStepIndex = computed(() => steps.value.findIndex((item) => item.value === step.value))
const currentRole = computed(() => step.value === 2 ? 'farmer' : 'farmAdmin')
const currentIds = computed(() => currentRole.value === 'farmer' ? form.plotIds : form.farmIds)
const resourceTitle = computed(() => currentRole.value === 'farmer' ? '选择申请管理的地块' : '选择申请管理的农场')
const resourceHint = computed(() => currentRole.value === 'farmer' ? '审核通过后，只能查看和操作已授权地块及其关联设备。' : '审核通过后，只能管理已授权农场中的地块、农户与设备。')
const resources = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  const source = currentRole.value === 'farmer'
    ? availablePlots.value.map((item) => ({ id: item.plotNo, title: item.name, code: item.plotNo, meta: `${availableFarms.value.find((farm) => farm.farmId === item.farmId)?.name || item.farmId} · ${item.crop || '暂未种植'} ${item.note || ''}`, detail: `所属农场 ${item.farmId}` }))
    : availableFarms.value.map((item) => ({ id: item.farmId, title: item.name, code: item.farmId, meta: `${item.city || item.address || '位置未填写'} · ${availablePlots.value.filter((plot) => plot.farmId === item.farmId).length} 个地块`, detail: `状态：${item.active === false ? '停用' : '可申请'}` }))
  return source.filter((item) => !q || `${item.title}${item.code}${item.meta}`.toLowerCase().includes(q))
})
const roleSummary = computed(() => form.roles.map((role) => role === 'farmer' ? '农户' : '农场管理员').join('、'))

onMounted(async () => {
  if (isMock) return
  try {
    const [farmResponse, plotResponse] = await Promise.all([getFarmList(), getPlotList({ registrable: true })])
    availableFarms.value = unwrapList(farmResponse).map(normalizeFarm).filter((item) => item.active)
    availablePlots.value = unwrapList(plotResponse).map((row) => ({
      ...row,
      plotNo: String(row.plotNo ?? row.plotId ?? row.plot_id ?? row.id),
      farmId: String(row.farmId ?? row.farm_id ?? ''),
      name: row.name || row.plotName || row.plot_name || '未命名地块',
      crop: row.crop || row.cropName || row.crop_name || '暂未种植',
      note: row.note || row.description || '',
    })).filter((item) => item.active !== false && item.Active !== false)
  } catch (error) {
    ElMessage.error(error.message || '可申请的农场和地块加载失败')
  }
})

function toggleRole(role) {
  const index = form.roles.indexOf(role)
  if (index >= 0) {
    if (form.roles.length === 1) return ElMessage.warning('请至少选择一种申请身份')
    form.roles.splice(index, 1)
    if (role === 'farmer') form.plotIds = []
    else form.farmIds = []
  } else form.roles.push(role)
}
function validateAccount() {
  if (!/^[a-zA-Z0-9_]{4,20}$/.test(form.username)) return '用户名需为 4—20 位字母、数字或下划线'
  if (!form.realName.trim()) return '请输入真实姓名'
  if (!/^1\d{10}$/.test(form.phone)) return '请输入正确的 11 位手机号'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) return '请输入正确的邮箱地址'
  if (form.password.length < 6 || form.password.length > 20) return '密码长度需为 6—20 位'
  if (form.password !== form.confirmPassword) return '两次输入的密码不一致'
  if (!form.roles.length) return '请至少选择一种申请身份'
  if (!form.agreement) return '请先阅读并同意用户服务协议'
  return ''
}
function nextFromAccount() {
  const message = validateAccount()
  if (message) return ElMessage.warning(message)
  keyword.value = ''
  step.value = form.roles.includes('farmer') ? 2 : 3
}
function toggleResource(id) {
  const ids = currentIds.value
  const index = ids.indexOf(id)
  if (index >= 0) ids.splice(index, 1)
  else ids.push(id)
}
function continueFromResource() {
  if (!currentIds.value.length) return ElMessage.warning(`请至少选择一个${currentRole.value === 'farmer' ? '地块' : '农场'}`)
  if (step.value === 2 && form.roles.includes('farmAdmin')) { keyword.value = ''; step.value = 3 }
  else submit()
}
function previousStep() { keyword.value = ''; step.value = step.value === 3 && form.roles.includes('farmer') ? 2 : 1 }
async function submit() {
  if (form.roles.includes('farmAdmin') && !form.farmIds.length) return ElMessage.warning('请至少选择一个农场')
  submitting.value = true
  try {
    await registrationStore.submitApplication({ username: form.username, realName: form.realName, phone: form.phone, email: form.email, password: form.password, roles: [...form.roles], plotIds: [...form.plotIds], farmIds: [...form.farmIds] })
    step.value = 4
  } catch (error) { ElMessage.error(error.message || '提交失败，请稍后重试') }
  finally { submitting.value = false }
}
</script>

<template>
  <div class="register-page">
    <header class="auth-header">
      <button class="brand" type="button" @click="router.push('/login')"><span>禾</span><strong>智慧农业监测平台</strong></button>
      <div class="login-link">已有账号？<el-button link type="primary" @click="router.push('/login')">返回登录</el-button></div>
    </header>

    <main class="register-shell">
      <div class="stepper" :style="{ gridTemplateColumns: `repeat(${steps.length}, 1fr)` }">
        <div v-for="(item, index) in steps" :key="item.value" :class="['step-item', { active: index <= currentStepIndex }]">
          <span>{{ index < currentStepIndex ? '✓' : index + 1 }}</span><label>{{ item.label }}</label>
        </div>
      </div>

      <section v-if="step === 1" class="register-card account-card">
        <div class="card-heading"><span class="heading-icon"><UserFilled /></span><div><h1>创建平台账号</h1><p>注册仅向农户和农场管理员开放，提交后需由系统管理员审核。</p></div></div>
        <div class="form-grid">
          <label><span>用户名</span><el-input v-model="form.username" size="large" maxlength="20" placeholder="4—20 位字母、数字或下划线" /></label>
          <label><span>真实姓名</span><el-input v-model="form.realName" size="large" maxlength="20" placeholder="请输入真实姓名" /></label>
          <label><span>手机号</span><el-input v-model="form.phone" size="large" maxlength="11" placeholder="用于接收审核通知" /></label>
          <label><span>邮箱</span><el-input v-model="form.email" size="large" placeholder="用于找回密码和接收告警" /></label>
          <label><span>密码</span><el-input v-model="form.password" size="large" type="password" show-password placeholder="6—20 位字符" /></label>
          <label><span>确认密码</span><el-input v-model="form.confirmPassword" size="large" type="password" show-password placeholder="请再次输入密码" /></label>
        </div>
        <div class="role-title"><strong>选择申请身份</strong><small>系统管理员账号由平台内部创建，不开放注册</small></div>
        <div class="role-grid">
          <button v-for="role in roleOptions" :key="role.value" type="button" :class="['role-card', { selected: form.roles.includes(role.value) }]" @click="toggleRole(role.value)">
            <span class="role-icon"><component :is="role.icon" /></span><span><strong>{{ role.label }}</strong><small>{{ role.description }}</small></span><i><CircleCheck /></i>
          </button>
        </div>
        <div class="agreement"><el-checkbox v-model="form.agreement">我已阅读并同意《用户服务协议》和《隐私政策》</el-checkbox></div>
        <div class="card-actions"><el-button size="large" @click="router.push('/login')">取消</el-button><el-button type="primary" size="large" @click="nextFromAccount">下一步：选择授权范围</el-button></div>
      </section>

      <section v-else-if="step === 2 || step === 3" class="register-card resource-card">
        <div class="resource-head"><div><p class="eyebrow">{{ currentRole === 'farmer' ? '农户权限申请' : '农场管理员权限申请' }}</p><h1>{{ resourceTitle }}</h1><p>{{ resourceHint }}</p></div><span class="selection-count">已选择 <b>{{ currentIds.length }}</b> 项</span></div>
        <el-input v-model="keyword" size="large" clearable :placeholder="`搜索${currentRole === 'farmer' ? '地块' : '农场'}名称或编号`"><template #prefix><el-icon><Search /></el-icon></template></el-input>
        <div class="resource-grid">
          <button v-for="item in resources" :key="item.id" type="button" :class="['resource-item', { selected: currentIds.includes(item.id) }]" @click="toggleResource(item.id)">
            <span class="resource-check"><CircleCheck /></span><span class="resource-symbol"><Collection /></span><span class="resource-copy"><strong>{{ item.title }}</strong><b>{{ item.code }}</b><small>{{ item.meta }}</small><em>{{ item.detail }}</em></span>
          </button>
        </div>
        <div class="audit-note"><el-icon><InfoFilled /></el-icon><span>所选范围不会立即生效。系统管理员审核通过后，平台才会授予对应角色和管理权限。</span></div>
        <div class="card-actions"><el-button size="large" @click="previousStep"><el-icon><ArrowLeft /></el-icon>上一步</el-button><el-button type="primary" size="large" :loading="submitting" @click="continueFromResource">{{ step === 2 && form.roles.includes('farmAdmin') ? '下一步：选择管理农场' : '提交注册申请' }}</el-button></div>
      </section>

      <section v-else class="register-card success-card">
        <span class="success-icon"><CircleCheck /></span><p class="eyebrow">APPLICATION SUBMITTED</p><h1>注册申请已提交</h1><p>系统管理员将审核你的身份和申请范围。审核通过后即可使用用户名 <b>{{ form.username }}</b> 登录。</p>
        <div class="summary"><span><small>申请身份</small><strong>{{ roleSummary }}</strong></span><span><small>申请范围</small><strong>{{ form.plotIds.length }} 个地块 · {{ form.farmIds.length }} 个农场</strong></span><span><small>当前状态</small><strong class="pending">待审核</strong></span></div>
        <el-button type="primary" size="large" @click="router.replace('/login')">返回登录</el-button>
      </section>
    </main>
  </div>
</template>

<style scoped>
.register-page{min-height:100vh;padding:0 32px 48px;background:radial-gradient(circle at 12% 8%,rgba(95,192,139,.18),transparent 30%),linear-gradient(150deg,#f2f8f5,#fbfcf7 55%,#f1f7f3);color:#17332b}.auth-header{height:76px;max-width:1180px;display:flex;align-items:center;justify-content:space-between;margin:auto}.brand{display:flex;align-items:center;gap:11px;border:0;color:#173f33;background:transparent;cursor:pointer}.brand span{width:38px;height:38px;display:grid;place-items:center;border-radius:11px;color:#103c2e;background:#65cd97;font-size:17px;font-weight:800}.brand strong{font-size:16px}.login-link{color:#72837c;font-size:13px}.register-shell{max-width:980px;margin:14px auto 0}.stepper{max-width:760px;display:grid;grid-template-columns:repeat(4,1fr);margin:0 auto 28px}.step-item{position:relative;display:flex;flex-direction:column;align-items:center;gap:7px;color:#9aaba4;font-size:12px}.step-item:not(:last-child)::after{position:absolute;top:15px;left:58%;width:84%;height:2px;content:'';background:#dce9e3}.step-item.active:not(:last-child)::after{background:#75bd99}.step-item span{position:relative;z-index:1;width:31px;height:31px;display:grid;place-items:center;border:2px solid #d6e5de;border-radius:50%;background:#f8fbf9;font-weight:700}.step-item.active{color:#247b58}.step-item.active span{border-color:#2c9368;color:#fff;background:#2c9368}.register-card{padding:34px 38px;border:1px solid #d7e8df;border-radius:24px;background:rgba(255,255,255,.92);box-shadow:0 20px 55px rgba(23,70,54,.1);backdrop-filter:blur(12px)}.card-heading{display:flex;align-items:center;gap:15px;margin-bottom:26px}.heading-icon{width:50px;height:50px;display:grid;place-items:center;flex:0 0 50px;border-radius:15px;color:#257e5a;background:#e3f4eb;font-size:25px}.register-card h1{margin:0;color:#17392e;font-size:27px}.register-card p{margin:7px 0 0;color:#788a83;line-height:1.65}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px 20px}.form-grid label>span{display:block;margin-bottom:8px;color:#3b574d;font-size:13px;font-weight:650}.role-title{display:flex;justify-content:space-between;gap:12px;margin:27px 0 12px}.role-title small{color:#98a59f}.role-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.role-card{position:relative;display:flex;align-items:center;gap:13px;padding:16px;border:1px solid #dce8e2;border-radius:14px;color:#314d43;background:#fbfdfc;text-align:left;cursor:pointer;transition:.2s}.role-card:hover,.role-card.selected{border-color:#54ad82;background:#f1faf5;box-shadow:0 7px 18px rgba(44,135,96,.09)}.role-icon{width:42px;height:42px;display:grid;place-items:center;flex:0 0 42px;border-radius:12px;color:#2b865f;background:#e4f4ec;font-size:21px}.role-card strong,.role-card small{display:block}.role-card small{margin-top:5px;color:#82918b;font-size:11px}.role-card i{margin-left:auto;color:#b9cac2;font-size:21px}.role-card.selected i{color:#2b9868}.agreement{margin:20px 0}.card-actions{display:flex;justify-content:flex-end;gap:10px;padding-top:20px;border-top:1px solid #edf2ef}.card-actions .el-button{min-width:150px}.resource-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:22px}.eyebrow{margin:0 0 6px!important;color:#2c9065!important;font-size:10px;font-weight:800;letter-spacing:2px}.selection-count{padding:9px 13px;border-radius:12px;color:#497164;background:#ecf7f1;font-size:12px}.selection-count b{color:#21825a;font-size:17px}.resource-grid{max-height:390px;display:grid;grid-template-columns:repeat(2,1fr);gap:13px;margin:18px 0;overflow:auto}.resource-item{position:relative;display:flex;align-items:center;gap:12px;padding:16px;border:1px solid #dde9e3;border-radius:15px;color:#29473d;background:#fbfdfc;text-align:left;cursor:pointer;transition:.2s}.resource-item:hover,.resource-item.selected{border-color:#55ac82;background:#f1faf5;box-shadow:0 8px 20px rgba(39,126,89,.08)}.resource-check{position:absolute;top:10px;right:10px;color:#c2d2ca;font-size:18px}.resource-item.selected .resource-check{color:#279263}.resource-symbol{width:42px;height:42px;display:grid;place-items:center;flex:0 0 42px;border-radius:12px;color:#327f60;background:#e5f3ec;font-size:20px}.resource-copy strong,.resource-copy small,.resource-copy em{display:block}.resource-copy b{margin-left:8px;color:#7f918a;font-size:11px}.resource-copy small{margin-top:5px;color:#657a71;font-size:11px}.resource-copy em{margin-top:4px;color:#9aa8a2;font-size:10px;font-style:normal}.audit-note{display:flex;align-items:flex-start;gap:8px;margin:5px 0 18px;padding:12px 14px;border-radius:12px;color:#6a7e75;background:#f2f7f4;font-size:12px;line-height:1.6}.audit-note .el-icon{margin-top:3px;color:#348c67}.success-card{max-width:700px;margin:auto;padding:58px;text-align:center}.success-icon{width:76px;height:76px;display:grid;place-items:center;margin:0 auto 19px;border-radius:50%;color:#fff;background:linear-gradient(145deg,#4db580,#247a58);box-shadow:0 12px 28px rgba(39,135,95,.25);font-size:42px}.success-card>p{max-width:520px;margin:10px auto}.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:28px 0}.summary span{padding:15px;border-radius:13px;background:#f3f8f5}.summary small,.summary strong{display:block}.summary small{color:#8b9a94;font-size:11px}.summary strong{margin-top:6px}.summary .pending{color:#b7792c}.success-card>.el-button{min-width:190px}@media(max-width:720px){.register-page{padding:0 16px 30px}.auth-header{height:66px}.login-link{font-size:0}.register-card{padding:24px 20px}.form-grid,.role-grid,.resource-grid{grid-template-columns:1fr}.role-title,.resource-head{flex-direction:column}.resource-grid{max-height:none}.card-actions .el-button{min-width:0;flex:1}.summary{grid-template-columns:1fr}.step-item label{font-size:10px}}
</style>
