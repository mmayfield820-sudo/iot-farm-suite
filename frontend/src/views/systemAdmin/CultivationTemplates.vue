<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createCultivationTemplate, deleteCultivationTemplate, getCultivationTemplates, updateCultivationTemplate } from '@/api/cultivation'

const loading = ref(false)
const rows = ref([])
const dialogVisible = ref(false)
const editingId = ref('')
const form = reactive({ templateCode: '', templateName: '', varietyName: '', region: '重庆市奉节县', version: 1, templateStatus: 'ACTIVE', templateContentText: '' })

const emptyContent = () => JSON.stringify({ crop: '脐橙', region: '重庆市奉节县', variety: '', treeClass: 'BEARING_TREE', maturityClass: '', periodDefinition: { EARLY: '1-10日', MID: '11-20日', LATE: '21日至月末' }, stageModelVersion: 'V1.1', moistureReferenceVersion: 'V1.1', moistureReferencePolicy: '定性农艺参考，不直接替代地块传感器阈值', stages: [{ code: 'SPRING_GROWTH', name: '萌芽与春季管理期', start: { month: 2, period: 'EARLY' }, end: { month: 3, period: 'LATE' }, priority: 50, canOverlap: false, managementFocus: [], soilMoistureReference: { type: 'QUALITATIVE', basis: 'FIELD_CAPACITY_RATIO', referenceText: '', irrigationTriggerReference: { below: 60, unit: '%', meaning: '' }, note: '' }, tasks: [] }] }, null, 2)

async function load() {
  loading.value = true
  try { rows.value = await getCultivationTemplates() }
  catch (error) { ElMessage.error(error.message || '模板加载失败') }
  finally { loading.value = false }
}

function openCreate() {
  editingId.value = ''
  Object.assign(form, { templateCode: '', templateName: '', varietyName: '', region: '重庆市奉节县', version: 1, templateStatus: 'ACTIVE', templateContentText: emptyContent() })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.templateId
  Object.assign(form, { ...row, templateContentText: JSON.stringify(row.templateContent, null, 2) })
  dialogVisible.value = true
}

async function save() {
  let templateContent
  try { templateContent = JSON.parse(form.templateContentText) }
  catch { ElMessage.error('模板规则不是有效 JSON'); return }
  const payload = { templateCode: form.templateCode, templateName: form.templateName, varietyName: form.varietyName, region: form.region, version: Number(form.version), templateStatus: form.templateStatus, templateContent }
  try {
    if (editingId.value) await updateCultivationTemplate(editingId.value, payload)
    else await createCultivationTemplate(payload)
    ElMessage.success(editingId.value ? '模板已更新' : '模板已创建')
    dialogVisible.value = false
    await load()
  } catch (error) { ElMessage.error(error.message || '模板保存失败') }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确认删除模板“${row.templateName}”吗？已绑定地块的模板不能删除。`, '删除模板', { type: 'warning' })
    await deleteCultivationTemplate(row.templateId)
    ElMessage.success('模板已删除')
    await load()
  } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message || '模板删除失败') }
}

onMounted(load)
</script>

<template>
  <div class="admin-template-page">
    <div class="page-head">
      <div><h1>脐橙管理模板</h1><p>维护不同品种和版本的年度管理阶段规则。</p></div>
      <el-button type="primary" @click="openCreate">新增模板</el-button>
    </div>
    <el-card shadow="never">
      <el-table v-loading="loading" :data="rows">
        <el-table-column prop="templateCode" label="模板编码" min-width="150" />
        <el-table-column prop="templateName" label="模板名称" min-width="250" />
        <el-table-column prop="varietyName" label="品种" min-width="130" />
        <el-table-column prop="region" label="适用地区" min-width="150" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.templateStatus === 'ACTIVE' ? 'success' : 'info'">{{ row.templateStatus === 'ACTIVE' ? '启用' : '停用' }}</el-tag></template></el-table-column>
        <el-table-column label="阶段数" width="90"><template #default="{ row }">{{ row.templateContent?.stages?.length || 0 }}</template></el-table-column>
        <el-table-column label="操作" width="150" fixed="right"><template #default="{ row }"><el-button link type="primary" @click="openEdit(row)">编辑</el-button><el-button link type="danger" @click="remove(row)">删除</el-button></template></el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑模板' : '新增模板'" width="760px">
      <el-form label-position="top">
        <div class="form-grid">
          <el-form-item label="模板编码"><el-input v-model="form.templateCode" /></el-form-item>
          <el-form-item label="模板名称"><el-input v-model="form.templateName" /></el-form-item>
          <el-form-item label="品种"><el-input v-model="form.varietyName" /></el-form-item>
          <el-form-item label="适用地区"><el-input v-model="form.region" /></el-form-item>
          <el-form-item label="版本"><el-input-number v-model="form.version" :min="1" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.templateStatus"><el-option label="启用" value="ACTIVE" /><el-option label="停用" value="INACTIVE" /></el-select></el-form-item>
        </div>
        <el-form-item label="模板规则 JSON"><el-input v-model="form.templateContentText" type="textarea" :rows="16" class="json-editor" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.admin-template-page{padding:8px}.page-head{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px}.page-head h1{margin:0;color:#4a240f;font-size:30px}.page-head p{color:#8a6752}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 18px}.json-editor:deep(textarea){font-family:Consolas,monospace;font-size:13px}@media(max-width:760px){.form-grid{grid-template-columns:1fr}}
</style>
