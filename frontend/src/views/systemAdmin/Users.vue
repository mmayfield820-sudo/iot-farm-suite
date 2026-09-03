<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { commitUserImport, downloadUserImportTemplate, previewUserImport } from '@/api/platform'
import { usePlatformStore } from '@/stores/platform'

const store = usePlatformStore()
const roleOptions = [{ value: 'farmer', label: '农户' }, { value: 'farm_admin', label: '农场管理员' }, { value: 'system_admin', label: '系统管理员' }]
const statusOptions = [{ value: 'pending_activation', label: '待激活' }, { value: 'active', label: '正常' }, { value: 'disabled', label: '已停用' }]
const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const keyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const form = reactive({ id: '', employeeNo: '', idCardNo: '', idCardMasked: '', name: '', phone: '', email: '', roleCodes: [], farmIds: [], plotIds: [] })
const rules = {
  employeeNo: [{ required: true, message: '请输入员工工号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入员工姓名', trigger: 'blur' }],
  roleCodes: [{ type: 'array', min: 1, message: '请至少分配一个角色', trigger: 'change' }],
}
const importDialogVisible = ref(false)
const importFiles = ref([])
const importFile = ref(null)
const importJob = ref(null)
const importLoading = ref(false)
const importCommitting = ref(false)

const availablePlots = computed(() => store.plots.filter((plot) => !form.farmIds.length || form.farmIds.includes(plot.farmId)))
const importReady = computed(() => importJob.value?.status === 'ready' && importJob.value.invalidRows === 0 && importJob.value.validRows > 0)

function statusTone(status) { return status === 'disabled' ? 'danger' : status === 'pending_activation' ? 'warning' : '' }
function statusLabel(status) { return statusOptions.find((item) => item.value === status)?.label || status }
function roleLabel(code) { return roleOptions.find((item) => item.value === code)?.label || code }
function scopeSummary(row) {
  const parts = []
  if (row.farmIds?.length) parts.push(`${row.farmIds.length} 个橙园`)
  if (row.plotIds?.length) parts.push(`${row.plotIds.length} 个地块`)
  return parts.join('、') || '全局或无指定范围'
}

async function loadUsers() {
  loading.value = true
  try {
    const result = await store.listUsers({ page: page.value, pageSize, keyword: keyword.value.trim(), role: roleFilter.value, status: statusFilter.value })
    users.value = result.items
    total.value = result.total
  } catch (error) { ElMessage.error(error.message || '账号列表加载失败') }
  finally { loading.value = false }
}
function searchUsers() { page.value = 1; loadUsers() }
function changePage(value) { page.value = value; loadUsers() }

function resetForm() {
  Object.assign(form, { id: '', employeeNo: '', idCardNo: '', idCardMasked: '', name: '', phone: '', email: '', roleCodes: [], farmIds: [], plotIds: [] })
  nextTick(() => formRef.value?.clearValidate())
}
function addUser() { resetForm(); dialogVisible.value = true }
function editUser(row) {
  Object.assign(form, { id: row.id, employeeNo: row.employeeNo, idCardNo: '', idCardMasked: row.idCardMasked || '', name: row.name, phone: row.phone || '', email: row.email || '', roleCodes: [...(row.roleCodes || [])], farmIds: [...(row.farmIds || [])], plotIds: [...(row.plotIds || [])] })
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

async function saveUser() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  if (!form.id && !/^\d{15}$|^\d{17}[\dXx]$/.test(form.idCardNo.trim())) return ElMessage.warning('请输入有效的 15 位或 18 位身份证号')
  if (form.id && form.idCardNo && !/^\d{15}$|^\d{17}[\dXx]$/.test(form.idCardNo.trim())) return ElMessage.warning('请输入有效的 15 位或 18 位身份证号')
  if (form.roleCodes.includes('farm_admin') && !form.farmIds.length) return ElMessage.warning('农场管理员至少需要授权一个橙园')
  if (form.roleCodes.includes('farmer') && !form.plotIds.length) return ElMessage.warning('农户至少需要授权一个地块')
  saving.value = true
  try {
    await store.saveUser({ ...form, farmIds: form.roleCodes.includes('farm_admin') ? [...form.farmIds] : [], plotIds: form.roleCodes.includes('farmer') ? [...form.plotIds] : [] })
    dialogVisible.value = false
    await loadUsers()
    ElMessage.success(form.id ? '账号与授权已更新' : '账号已预置，初始密码为身份证号后六位')
  } catch (error) {
    const message = error.message === 'EMPLOYEE_NO_OR_ID_CARD_EXISTS' ? '工号或身份证信息已存在' : error.message === 'PLOT_ALREADY_ASSIGNED' ? '所选地块已授权给其他农户' : error.message
    ElMessage.error(message || '账号保存失败')
  } finally { saving.value = false }
}

async function toggleUser(row) {
  const enabling = row.status === 'disabled'
  const action = enabling ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(enabling ? `确认启用账号 ${row.employeeNo}？` : `停用后 ${row.name} 将无法登录，已有角色、授权范围和操作记录会保留。确认继续？`, `${action}账号`, { type: enabling ? 'success' : 'warning', confirmButtonText: `确认${action}`, cancelButtonText: '取消' })
    await store.toggleUser(row.id)
    await loadUsers()
    ElMessage.success(`账号已${action}`)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message === 'CANNOT_DISABLE_CURRENT_USER' ? '不能停用当前登录账号' : error.message || `${action}账号失败`)
  }
}

async function resetPassword(row) {
  try {
    await ElMessageBox.confirm(`重置后，${row.name} 需要使用身份证号后六位重新登录并设置正式密码。`, '重置初始密码', { type: 'warning', confirmButtonText: '确认重置', cancelButtonText: '取消' })
    await store.resetPassword(row.id)
    await loadUsers()
    ElMessage.success('初始密码已重置，账号状态已变为待激活')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message === 'USER_NOT_FOUND' ? '该账号没有可重置的初始密码' : error.message || '初始密码重置失败')
  }
}

async function downloadTemplate() {
  try {
    const blob = await downloadUserImportTemplate()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '员工账号导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (error) { ElMessage.error(error.message || '导入模板下载失败') }
}
function openImport() { importFiles.value = []; importFile.value = null; importJob.value = null; importDialogVisible.value = true }
function changeImportFile(file, files) { importFiles.value = files.slice(-1); importFile.value = file.raw || null; importJob.value = null }
function removeImportFile() { importFile.value = null; importJob.value = null }
function exceedImportFile(files) {
  importFiles.value = []
  if (files[0]) changeImportFile({ name: files[0].name, raw: files[0] }, [{ name: files[0].name, raw: files[0] }])
}
async function previewImport() {
  if (!importFile.value) return ElMessage.warning('请先选择 Excel 文件')
  if (!importFile.value.name.toLowerCase().endsWith('.xlsx')) return ElMessage.warning('仅支持 .xlsx 文件')
  if (importFile.value.size > 5 * 1024 * 1024) return ElMessage.warning('文件大小不能超过 5 MB')
  importLoading.value = true
  try { importJob.value = await previewUserImport(importFile.value) }
  catch (error) { ElMessage.error(error.message || 'Excel 预校验失败') }
  finally { importLoading.value = false }
}
async function confirmImport() {
  if (!importReady.value) return
  importCommitting.value = true
  try {
    importJob.value = await commitUserImport(importJob.value.id)
    await loadUsers()
    ElMessage.success(`成功导入 ${importJob.value.validRows} 个员工账号`)
  } catch (error) { ElMessage.error(error.message || '确认导入失败') }
  finally { importCommitting.value = false }
}
function importErrorText(error) {
  const labels = { REQUIRED_FIELD_MISSING: '必填字段缺失', DUPLICATE_IMPORT_VALUE: '文件内存在重复工号或身份证号', EMPLOYEE_NO_OR_ID_CARD_EXISTS: '工号或身份证信息已存在', PLOT_ALREADY_ASSIGNED: '地块已授权给其他农户', FARM_SCOPE_REQUIRED: '农场管理员缺少橙园授权', PLOT_SCOPE_REQUIRED: '农户缺少地块授权', INVALID_ROLE: '角色编码无效' }
  return labels[error.code] || error.message || error.code
}

onMounted(loadUsers)
</script>

<template>
  <div class="farmer-page users-page">
    <div class="page-head"><div><h1 class="page-title">用户管理</h1><p class="page-subtitle">预置员工账号，维护角色与数据授权范围。</p></div><div class="page-actions"><el-button @click="openImport"><el-icon><Upload /></el-icon>Excel 批量导入</el-button><el-button type="primary" @click="addUser"><el-icon><Plus /></el-icon>新增账号</el-button></div></div>
    <section class="content-panel users-panel">
      <div class="section-head"><div><h3>账号列表</h3><p>共 {{ total }} 个员工账号</p></div><div class="table-toolbar"><el-select v-model="roleFilter" clearable placeholder="全部角色" @change="searchUsers"><el-option v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select><el-select v-model="statusFilter" clearable placeholder="全部状态" @change="searchUsers"><el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select><el-input v-model="keyword" clearable placeholder="搜索工号、姓名或手机号" @keyup.enter="searchUsers" @clear="searchUsers"><template #prefix><el-icon><Search /></el-icon></template></el-input><el-tooltip content="查询账号" placement="top"><el-button aria-label="查询账号" @click="searchUsers"><el-icon><Search /></el-icon></el-button></el-tooltip></div></div>
      <el-table v-loading="loading" :data="users" class="compact-table" row-key="id"><el-table-column prop="employeeNo" label="员工工号" width="130" /><el-table-column prop="name" label="姓名" width="110"><template #default="scope"><strong class="user-name">{{ scope.row.name }}</strong></template></el-table-column><el-table-column label="身份信息" min-width="160"><template #default="scope">{{ scope.row.idCardMasked || '未录入' }}</template></el-table-column><el-table-column label="联系方式" min-width="190"><template #default="scope"><span class="contact"><b>{{ scope.row.phone || '未填写手机号' }}</b><small>{{ scope.row.email || '未填写邮箱' }}</small></span></template></el-table-column><el-table-column label="角色" min-width="190"><template #default="scope"><el-tag v-for="code in scope.row.roleCodes" :key="code" size="small" class="role-tag" effect="plain">{{ roleLabel(code) }}</el-tag></template></el-table-column><el-table-column label="授权范围" min-width="150"><template #default="scope">{{ scopeSummary(scope.row) }}</template></el-table-column><el-table-column label="状态" width="100"><template #default="scope"><span :class="['status-pill', statusTone(scope.row.status)]">{{ statusLabel(scope.row.status) }}</span></template></el-table-column><el-table-column label="操作" fixed="right" width="245" align="right"><template #default="scope"><el-button link type="primary" @click="editUser(scope.row)"><el-icon><EditPen /></el-icon>编辑</el-button><el-button link @click="resetPassword(scope.row)">重置初始密码</el-button><el-button link :type="scope.row.status === 'disabled' ? 'success' : 'danger'" @click="toggleUser(scope.row)">{{ scope.row.status === 'disabled' ? '启用' : '停用' }}</el-button></template></el-table-column><template #empty><el-empty description="暂无符合条件的员工账号" :image-size="72" /></template></el-table>
      <div v-if="total > pageSize" class="pagination"><el-pagination background layout="prev, pager, next" :current-page="page" :page-size="pageSize" :total="total" @current-change="changePage" /></div>
    </section>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑账号与授权' : '新增预置账号'" width="min(700px, calc(100vw - 32px))" destroy-on-close><el-form ref="formRef" :model="form" :rules="rules" label-position="top"><div class="form-grid"><el-form-item label="员工工号" prop="employeeNo"><el-input v-model="form.employeeNo" :disabled="Boolean(form.id)" maxlength="50" placeholder="作为首次登录账号" /></el-form-item><el-form-item label="员工姓名" prop="name"><el-input v-model="form.name" maxlength="50" /></el-form-item><el-form-item label="身份证号" :required="!form.id"><el-input v-model="form.idCardNo" maxlength="18" :placeholder="form.id ? `已保存 ${form.idCardMasked || '身份摘要'}，留空则不修改` : '仅用于身份摘要和生成初始密码'" /></el-form-item><el-form-item label="手机号"><el-input v-model="form.phone" maxlength="20" /></el-form-item><el-form-item class="full-row" label="邮箱"><el-input v-model="form.email" maxlength="100" /></el-form-item><el-form-item class="full-row" label="角色" prop="roleCodes"><el-checkbox-group v-model="form.roleCodes"><el-checkbox-button v-for="item in roleOptions" :key="item.value" :value="item.value">{{ item.label }}</el-checkbox-button></el-checkbox-group></el-form-item><el-form-item v-if="form.roleCodes.includes('farm_admin')" class="full-row" label="授权橙园"><el-select v-model="form.farmIds" multiple clearable filterable placeholder="请选择农场管理员可管理的橙园"><el-option v-for="farm in store.farms.filter((item) => item.status === 'active')" :key="farm.farmId" :label="`${farm.farmId} · ${farm.name}`" :value="farm.farmId" /></el-select></el-form-item><el-form-item v-if="form.roleCodes.includes('farmer')" class="full-row" label="授权地块"><el-select v-model="form.plotIds" multiple clearable filterable placeholder="请选择农户负责的地块"><el-option v-for="plot in availablePlots.filter((item) => item.status !== 'inactive')" :key="plot.plotNo" :label="`${plot.code || plot.plotNo} · ${plot.name}`" :value="plot.plotNo" /></el-select></el-form-item></div><p class="identity-note"><el-icon><Lock /></el-icon>身份证号明文不会保存；新账号使用身份证号后六位作为初始密码，首次登录时必须修改。</p></el-form><template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveUser">保存账号</el-button></template></el-dialog>

    <el-dialog v-model="importDialogVisible" title="Excel 批量导入账号" width="min(720px, calc(100vw - 32px))" destroy-on-close><div class="import-actions"><div><strong>员工账号导入</strong><p>请使用标准模板填写工号、身份信息、角色及授权范围。</p></div><el-button @click="downloadTemplate"><el-icon><Download /></el-icon>下载模板</el-button></div><el-upload v-model:file-list="importFiles" drag :auto-upload="false" :limit="1" accept=".xlsx" :on-change="changeImportFile" :on-remove="removeImportFile" :on-exceed="exceedImportFile"><el-icon class="upload-icon"><UploadFilled /></el-icon><div class="el-upload__text">拖放 Excel 文件到此处，或<em>点击选择</em></div><template #tip><span>仅支持 .xlsx，文件不超过 5 MB。上传后先进行预校验，不会立即写入账号。</span></template></el-upload><div v-if="importJob" :class="['import-result', importJob.invalidRows ? 'has-errors' : 'ready']"><div class="import-summary"><span><small>总行数</small><strong>{{ importJob.totalRows }}</strong></span><span><small>校验通过</small><strong>{{ importJob.validRows }}</strong></span><span><small>失败行</small><strong>{{ importJob.invalidRows }}</strong></span></div><el-table v-if="importJob.errors?.length" :data="importJob.errors" max-height="220"><el-table-column prop="rowNumber" label="Excel 行号" width="100" /><el-table-column prop="field" label="字段" width="110" /><el-table-column label="失败原因" min-width="260"><template #default="scope">{{ importErrorText(scope.row) }}</template></el-table-column></el-table><p v-else><el-icon><CircleCheckFilled /></el-icon>所有数据已通过校验，可以确认导入。</p></div><template #footer><el-button @click="importDialogVisible = false">关闭</el-button><el-button :loading="importLoading" :disabled="!importFile" @click="previewImport">上传并预校验</el-button><el-button type="primary" :loading="importCommitting" :disabled="!importReady" @click="confirmImport">确认导入</el-button></template></el-dialog>
  </div>
</template>

<style scoped>
.users-page>.page-head{align-items:center;margin-bottom:18px}.users-page .page-subtitle{margin-bottom:0}.users-panel{padding:20px 0 0;overflow:hidden}.users-panel .section-head{align-items:center;padding:0 20px}.table-toolbar{display:flex;gap:10px}.table-toolbar>.el-select{width:138px}.table-toolbar>.el-input{width:240px}.user-name{color:#29473d}.contact b,.contact small{display:block}.contact b{font-weight:500}.contact small{margin-top:4px;color:#8a9893}.role-tag{margin:2px 4px 2px 0}.pagination{display:flex;justify-content:flex-end;padding:18px 20px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}.form-grid .full-row{grid-column:1/-1}.form-grid .el-select{width:100%}.identity-note{display:flex;align-items:flex-start;gap:7px;margin:2px 0 0;padding:11px 13px;border-radius:8px;color:#62766d;background:#f3f7f5;font-size:12px;line-height:1.6}.identity-note .el-icon{margin-top:3px;color:#377e60}.import-actions{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:18px}.import-actions strong{font-size:15px}.import-actions p{margin:5px 0 0;color:#7c8c85;font-size:12px}.upload-icon{font-size:42px;color:#629d83}.import-result{margin-top:18px;padding:16px;border:1px solid #dbe9e2;border-radius:8px;background:#f7fbf9}.import-result.has-errors{border-color:#efd3d3;background:#fff9f9}.import-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}.import-summary span{padding:10px 12px;border-radius:7px;background:#fff}.import-summary small,.import-summary strong{display:block}.import-summary small{color:#82928b}.import-summary strong{margin-top:4px;font-size:20px}.import-result>p{display:flex;align-items:center;gap:7px;margin:0;color:#2f805e}.import-result>p .el-icon{font-size:18px}@media(max-width:900px){.users-page>.page-head{align-items:flex-start}.users-page>.page-head>.page-actions{width:100%}.users-page>.page-head>.page-actions .el-button{flex:1}.users-panel .section-head{align-items:flex-start;flex-direction:column}.table-toolbar{width:100%;flex-wrap:wrap}.table-toolbar>.el-select,.table-toolbar>.el-input{width:100%}.form-grid{grid-template-columns:1fr}.form-grid .full-row{grid-column:auto}.import-actions{align-items:flex-start;flex-direction:column}.pagination{justify-content:center}}
</style>
