<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ROLE_LABEL } from '@/stores/user'
import { usePlatformStore } from '@/stores/platform'
import { useRegistrationStore } from '@/stores/registration'

const store = usePlatformStore()
const registrationStore = useRegistrationStore()
const keyword = ref('')
const activeTab = ref(registrationStore.pendingCount ? 'review' : 'accounts')
const dialog = ref(false)
const form = reactive({ id: '', username: '', name: '', email: '', roles: [], farmScope: [], plotScope: [] })
const users = computed(() => store.users.filter((item) => !keyword.value || `${item.id}${item.username}${item.name}`.toLowerCase().includes(keyword.value.toLowerCase())))
const applications = computed(() => registrationStore.applications)
onMounted(async () => {
  try {
    await registrationStore.loadApplications()
    if (registrationStore.pendingCount) activeTab.value = 'review'
  } catch (error) { ElMessage.error(error.message || '注册申请加载失败') }
})

function edit(row) {
  const copy = JSON.parse(JSON.stringify(row))
  copy.farmScope = Array.isArray(copy.farmScope) ? copy.farmScope : String(copy.farmScope === '-' ? '' : copy.farmScope || '').split(',').map((item) => item.trim()).filter(Boolean)
  copy.plotScope = Array.isArray(copy.plotScope) ? copy.plotScope : String(copy.plotScope === '-' ? '' : copy.plotScope || '').split(',').map((item) => item.trim()).filter(Boolean)
  Object.assign(form, copy)
  dialog.value = true
}
function add() { Object.assign(form, { id: '', username: '', name: '', email: '', roles: [], farmScope: [], plotScope: [] }); dialog.value = true }
async function save() {
  if (!form.username || !form.roles.length) return ElMessage.warning('请填写用户名并至少分配一个角色')
  try { await store.saveUser({ ...form }); dialog.value = false; ElMessage.success('账号信息已保存') } catch (error) { ElMessage.error(error.message || '账号保存失败') }
}
function toggle(row) {
  ElMessageBox.confirm(`确认${row.status === '正常' ? '禁用' : '恢复'}账号 ${row.username}？`, '账号状态变更', { type: 'warning' })
    .then(async () => { try { await store.toggleUser(row.id); ElMessage.success('账号状态已更新') } catch (error) { ElMessage.error(error.message || '状态更新失败') } })
}
function reset(row) {
  ElMessageBox.confirm(`将为 ${row.username} 生成临时密码，确认继续？`, '重置密码', { type: 'warning' })
    .then(async () => { try { await store.resetPassword(row.id); ElMessage.success('密码重置请求已提交') } catch (error) { ElMessage.error(error.message || '密码重置失败') } })
}
function resourceNames(application) {
  const parts = []
  if (application.roles.includes('farmer')) parts.push(`农户地块：${application.plotIds.map((id) => store.plots.find((item) => item.plotNo === id)?.name || id).join('、')}`)
  if (application.roles.includes('farmAdmin')) parts.push(`管理农场：${application.farmIds.map((id) => store.farms.find((item) => item.farmId === id)?.name || id).join('、')}`)
  return parts.join('；')
}
function approve(application) {
  const roleText = application.roles.map((role) => ROLE_LABEL[role]).join('、')
  ElMessageBox.confirm(`确认通过 ${application.realName} 的${roleText}注册申请？`, '审核注册申请', { type: 'success', confirmButtonText: '通过申请' })
    .then(async () => {
      const result = await registrationStore.approveApplication(application.id)
      if (!result) return
      if (result.account) {
        await store.saveUser({
          username: application.username,
          name: application.realName,
          email: application.email,
          roles: application.roles.map((role) => ROLE_LABEL[role]),
          farmScope: application.farmIds,
          plotScope: application.plotIds,
        })
      } else await store.loadData(true)
      ElMessage.success('申请已通过，账号现在可以登录')
    })
}
function reject(application) {
  ElMessageBox.prompt('请填写拒绝原因，申请人可修改资料后重新提交。', '拒绝注册申请', { inputPlaceholder: '例如：身份资料不完整', inputValidator: (value) => Boolean(value?.trim()) || '拒绝原因不能为空', confirmButtonText: '确认拒绝' })
    .then(async ({ value }) => { await registrationStore.rejectApplication(application.id, value.trim()); ElMessage.success('已拒绝该申请') })
}
</script>

<template>
  <div class="farmer-page">
    <div class="page-head"><div><h1 class="page-title">用户与注册审核</h1><p class="page-subtitle">维护账号角色和访问范围，审核农户及农场管理员的注册申请。</p></div></div>
    <section class="content-panel users-panel">
      <el-tabs v-model="activeTab">
        <el-tab-pane name="accounts" label="账号列表">
          <div class="table-toolbar"><el-input v-model="keyword" clearable placeholder="搜索用户"><template #prefix><el-icon><Search /></el-icon></template></el-input><el-button type="primary" @click="add"><el-icon><Plus /></el-icon>新增账号</el-button></div>
          <el-table :data="users" class="compact-table"><el-table-column prop="id" label="用户ID" width="90"/><el-table-column prop="username" label="用户名" min-width="120"/><el-table-column prop="name" label="姓名" width="90"/><el-table-column prop="email" label="邮箱" min-width="180"><template #default="scope">{{ scope.row.email || '未设置' }}</template></el-table-column><el-table-column label="角色" min-width="210"><template #default="scope"><el-tag v-for="role in scope.row.roles" :key="role" size="small" class="role-tag">{{ role }}</el-tag></template></el-table-column><el-table-column prop="farmScope" label="农场范围" min-width="110"/><el-table-column prop="plotScope" label="农户地块" min-width="110"/><el-table-column prop="status" label="状态" width="85"><template #default="scope"><span :class="['status-pill', scope.row.status === '禁用' ? 'danger' : '']">{{ scope.row.status }}</span></template></el-table-column><el-table-column label="操作" fixed="right" width="210"><template #default="scope"><el-button link type="primary" @click="edit(scope.row)">编辑</el-button><el-button link @click="reset(scope.row)">重置密码</el-button><el-button link :type="scope.row.status === '正常' ? 'danger' : 'success'" @click="toggle(scope.row)">{{ scope.row.status === '正常' ? '禁用' : '恢复' }}</el-button></template></el-table-column></el-table>
        </el-tab-pane>
        <el-tab-pane name="review"><template #label><span class="review-tab">注册审核<el-badge v-if="registrationStore.pendingCount" :value="registrationStore.pendingCount" /></span></template>
          <div v-if="applications.length" class="application-list">
            <article v-for="application in applications" :key="application.id" class="application-card">
              <div class="applicant-avatar">{{ application.realName?.slice(0, 1) }}</div>
              <div class="application-main"><div class="application-title"><strong>{{ application.realName }}</strong><span>{{ application.username }}</span><el-tag v-for="role in application.roles" :key="role" :type="role === 'farmer' ? 'success' : 'warning'" effect="light">{{ ROLE_LABEL[role] }}</el-tag><el-tag :type="application.status === '待审核' ? 'warning' : application.status === '已通过' ? 'success' : 'danger'" effect="plain">{{ application.status }}</el-tag></div><p>{{ application.phone }} · {{ application.email }}</p><div class="scope-line"><b>申请范围</b><span>{{ resourceNames(application) }}</span></div><small>提交时间：{{ application.createdAt }}<template v-if="application.reviewedAt">　审核时间：{{ application.reviewedAt }}</template></small><div v-if="application.rejectReason" class="reject-reason">拒绝原因：{{ application.rejectReason }}</div></div>
              <div v-if="application.status === '待审核'" class="review-actions"><el-button type="success" @click="approve(application)">通过</el-button><el-button type="danger" plain @click="reject(application)">拒绝</el-button></div>
            </article>
          </div>
          <el-empty v-else description="暂无注册申请" />
        </el-tab-pane>
      </el-tabs>
    </section>

<el-dialog v-model="dialog" :title="form.id ? '编辑账号' : '新增账号'" width="560px"><el-form label-position="top"><div class="form-grid"><el-form-item label="用户名"><el-input v-model="form.username" :disabled="Boolean(form.id)"/></el-form-item><el-form-item label="姓名"><el-input v-model="form.name"/></el-form-item></div><el-form-item label="邮箱"><el-input v-model="form.email" placeholder="可为空，用于接收告警邮件"/></el-form-item><el-form-item label="角色（可多选）"><el-checkbox-group v-model="form.roles"><el-checkbox-button v-for="role in ['农户','农场管理员','系统管理员']" :key="role" :value="role">{{ role }}</el-checkbox-button></el-checkbox-group></el-form-item><div class="form-grid"><el-form-item label="可访问农场"><el-select v-model="form.farmScope" multiple clearable style="width:100%"><el-option v-for="farm in store.farms" :key="farm.farmId" :label="`${farm.farmId} · ${farm.name}`" :value="farm.farmId"/></el-select></el-form-item><el-form-item label="农户地块"><el-select v-model="form.plotScope" multiple clearable style="width:100%"><el-option v-for="plot in store.plots.filter((item) => !form.farmScope.length || form.farmScope.includes(item.farmId))" :key="plot.plotNo" :label="`${plot.plotNo} · ${plot.name}`" :value="plot.plotNo"/></el-select></el-form-item></div></el-form><template #footer><el-button @click="dialog = false">取消</el-button><el-button type="primary" @click="save">保存账号</el-button></template></el-dialog>
  </div>
</template>

<style scoped>
.users-panel{padding-top:8px}.table-toolbar{display:flex;justify-content:flex-end;gap:10px;margin:8px 0 16px}.table-toolbar .el-input{width:220px}.role-tag{margin:2px 4px 2px 0}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.review-tab{display:inline-flex;align-items:center;gap:9px}.application-list{display:grid;gap:12px;padding:10px 0}.application-card{display:flex;align-items:flex-start;gap:15px;padding:18px;border:1px solid #e0eae5;border-radius:15px;background:#fbfdfc}.applicant-avatar{width:44px;height:44px;display:grid;place-items:center;flex:0 0 44px;border-radius:13px;color:#277c59;background:#e4f4eb;font-size:18px;font-weight:800}.application-main{min-width:0;flex:1}.application-title{display:flex;align-items:center;flex-wrap:wrap;gap:8px}.application-title strong{font-size:15px}.application-title>span{color:#85948e;font-size:12px}.application-main p{margin:6px 0;color:#75867f;font-size:12px}.scope-line{display:flex;gap:9px;margin:10px 0;padding:10px 12px;border-radius:10px;background:#f1f7f4;font-size:12px}.scope-line b{color:#35614f}.scope-line span{color:#5f746b}.application-main small{color:#9aa7a2}.reject-reason{margin-top:9px;color:#ae5555;font-size:12px}.review-actions{display:flex;gap:8px}@media(max-width:700px){.form-grid{grid-template-columns:1fr}.application-card{flex-wrap:wrap}.review-actions{width:100%;justify-content:flex-end}.table-toolbar{flex-direction:column}.table-toolbar .el-input{width:100%}}
</style>
