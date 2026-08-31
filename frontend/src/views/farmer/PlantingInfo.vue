<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getCultivationTemplates, getPlotPlanting, updatePlotPlanting, updatePlotStage } from '@/api/cultivation'
import { useFarmerStore } from '@/stores/farmer'

const store = useFarmerStore()
const plot = computed(() => store.currentPlot)
const loading = ref(false)
const planting = ref(null)
const templates = ref([])
const editVisible = ref(false)
const stageVisible = ref(false)
const form = reactive({ templateId: '', plantingDate: '', soilType: '', plantingRemark: '' })
const stageForm = reactive({ stageCode: '', reason: '' })
const selectedTemplate = computed(() => templates.value.find((item) => item.templateId === planting.value?.templateId))
const stageOptions = computed(() => selectedTemplate.value?.templateContent?.stages || [])

async function load() {
  if (!store.selectedPlotId) return
  loading.value = true
  try {
    const [plantingResult, templateResult] = await Promise.all([getPlotPlanting(store.selectedPlotId), getCultivationTemplates()])
    planting.value = plantingResult
    templates.value = templateResult.filter((item) => item.templateStatus === 'ACTIVE')
  } catch (error) { planting.value = null; ElMessage.error(error.message || '种植信息加载失败') }
  finally { loading.value = false }
}

function openEdit() {
  Object.assign(form, { templateId: planting.value.templateId, plantingDate: planting.value.plantingDate, soilType: planting.value.soilType || '', plantingRemark: planting.value.plantingRemark || '' })
  editVisible.value = true
}

async function savePlanting() {
  try {
    const result = await updatePlotPlanting(store.selectedPlotId, form)
    planting.value = result
    store.touchTimeline()
    editVisible.value = false
    ElMessage.success(result.regenerationRecommended ? '种植信息已更新，建议重新生成管理计划' : '种植信息已更新')
  } catch (error) { ElMessage.error(error.message || '保存失败') }
}

function openStage() { stageForm.stageCode = planting.value.currentStage?.stageCode || ''; stageForm.reason = ''; stageVisible.value = true }
async function saveStage() {
  if (!stageForm.reason.trim()) { ElMessage.warning('请填写现场修正原因'); return }
  try {
    const result = await updatePlotStage(store.selectedPlotId, stageForm)
    store.touchTimeline()
    stageVisible.value = false
    ElMessage.success(result.message)
    await load()
  } catch (error) { ElMessage.error(error.message || '阶段修正失败') }
}

watch(() => store.selectedPlotId, load, { immediate: true })
</script>

<template>
  <el-card v-loading="loading" shadow="never" class="planting-card">
    <template #header><div class="card-head"><div><div class="title-row"><h2>种植信息与当前阶段</h2><span v-if="plot" class="plot-code">{{ plot.plotId }}</span></div><p>根据模板和当前日期计算年度管理阶段。</p></div><div><el-button @click="openStage" :disabled="!planting">人工修正阶段</el-button><el-button type="primary" @click="openEdit" :disabled="!planting">编辑种植信息</el-button></div></div></template>
    <el-empty v-if="!planting && !loading" description="该地块尚未配置种植信息" />
    <div v-else-if="planting" class="planting-grid">
      <div class="stage-panel"><span class="eyebrow">当前生长阶段</span><strong>{{ planting.currentStage?.stageName || '暂无法判断' }}</strong><el-tag :type="planting.currentStage?.stageSource === 'OVERRIDE' ? 'warning' : 'success'">{{ planting.currentStage?.stageSource === 'OVERRIDE' ? '人工修正' : '系统计算' }}</el-tag><small v-if="planting.stageOverrideReason">修正原因：{{ planting.stageOverrideReason }}</small></div>
      <dl><div><dt>管理模板</dt><dd>{{ planting.templateName }} · V{{ planting.templateVersion }}</dd></div><div><dt>品种</dt><dd>{{ planting.varietyName }}</dd></div><div><dt>所属农场</dt><dd>{{ plot?.farmName || '-' }}</dd></div><div><dt>定植日期</dt><dd>{{ planting.plantingDate }}</dd></div><div><dt>树龄</dt><dd>{{ planting.currentStage?.treeAgeYears ?? '-' }} 年</dd></div><div><dt>位置</dt><dd>{{ plot?.location || '-' }}</dd></div><div><dt>土壤类型</dt><dd>{{ planting.soilType || '-' }}</dd></div><div><dt>种植备注</dt><dd>{{ planting.plantingRemark || '-' }}</dd></div><div><dt>最近灌溉</dt><dd>{{ plot?.lastIrrigation || '暂无记录' }}</dd></div></dl>
    </div>

    <el-dialog v-model="editVisible" title="编辑种植信息" width="560px">
      <el-form label-position="top"><el-form-item label="管理模板"><el-select v-model="form.templateId" style="width:100%"><el-option v-for="item in templates" :key="item.templateId" :label="`${item.templateName} · V${item.version}`" :value="item.templateId" /></el-select></el-form-item><el-form-item label="定植日期"><el-date-picker v-model="form.plantingDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item><el-form-item label="土壤类型"><el-input v-model="form.soilType" /></el-form-item><el-form-item label="备注"><el-input v-model="form.plantingRemark" type="textarea" :rows="3" /></el-form-item></el-form>
      <template #footer><el-button @click="editVisible=false">取消</el-button><el-button type="primary" @click="savePlanting">保存</el-button></template>
    </el-dialog>
    <el-dialog v-model="stageVisible" title="人工修正当前阶段" width="520px">
      <el-alert title="人工修正后应重新预览并生成管理计划。" type="warning" :closable="false" show-icon />
      <el-form label-position="top" class="stage-form"><el-form-item label="目标阶段"><el-select v-model="stageForm.stageCode" style="width:100%"><el-option v-for="item in stageOptions" :key="item.code" :label="item.name" :value="item.code" /></el-select></el-form-item><el-form-item label="现场判断原因（必填）"><el-input v-model="stageForm.reason" type="textarea" :rows="4" maxlength="255" show-word-limit /></el-form-item></el-form>
      <template #footer><el-button @click="stageVisible=false">取消</el-button><el-button type="primary" @click="saveStage">确认修正</el-button></template>
    </el-dialog>
  </el-card>
</template>

<style scoped>
.planting-card{margin-bottom:20px;border-color:#ecd8c8}.card-head{display:flex;justify-content:space-between;gap:16px;align-items:center}.title-row{display:flex;align-items:center;gap:12px}.card-head h2{margin:0;color:#4b2815}.plot-code{padding:5px 11px;border-radius:8px;color:#805d45;background:#fff0db;font-size:14px;font-weight:700}.card-head p{margin:6px 0 0;color:#98735d}.planting-grid{display:grid;grid-template-columns:280px 1fr;gap:28px}.stage-panel{min-height:210px;padding:24px;border-radius:18px;background:linear-gradient(135deg,#fff1df,#ffe0b8);display:flex;flex-direction:column;align-items:flex-start;gap:10px}.stage-panel strong{font-size:25px;color:#a8490b}.stage-panel small{color:#8b5b3d}.eyebrow{font-size:13px;color:#b55b1d}dl{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 28px;margin:0}dl>div{min-width:0;padding:13px 0;border-bottom:1px solid #f0e4db}dt{color:#98735d;font-size:13px}dd{overflow-wrap:anywhere;margin:5px 0 0;color:#432516;font-weight:600}.stage-form{margin-top:18px}@media(max-width:1100px){dl{grid-template-columns:1fr 1fr}}@media(max-width:850px){.planting-grid{grid-template-columns:1fr}.stage-panel{min-height:auto}.card-head{align-items:flex-start;flex-direction:column}dl{grid-template-columns:1fr}}
</style>
