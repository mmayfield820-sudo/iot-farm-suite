<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { generateFarmPlans, getFarmAnnualProduction, getFarmPlantingSchedule, listCropTemplates, listFarms, saveFarmPlantingSchedule } from '@/api/production'

const farms = ref([])
const templates = ref([])
const selectedFarmId = ref('')
const context = ref(null)
const plantingSchedule = ref(null)
const loading = ref(false)
const generating = ref(false)
const saving = ref(false)
const setupOpen = ref(false)
const form = reactive({ templateVersionId: '', plannedPlantingDate: '' })

const selectedFarm = computed(() => farms.value.find((item) => item.id === selectedFarmId.value))
const trackLabel = computed(() => context.value?.track === 'young' ? '幼树轨道' : '结果树轨道')
const currentStageCode = computed(() => context.value?.stage?.code)

function dateRange(stage) { return `${stage.startsOn.slice(5).replace('-', '月')}日 - ${stage.endsOn.slice(5).replace('-', '月')}日` }
async function loadContext() {
  context.value = null
  plantingSchedule.value = null
  form.templateVersionId = ''
  form.plannedPlantingDate = ''
  if (!selectedFarmId.value) return
  try {
    context.value = await getFarmAnnualProduction(selectedFarmId.value)
    form.templateVersionId = context.value.templateVersionId
    form.plannedPlantingDate = context.value.plantingDate
  } catch (error) {
    if (![404, 409].includes(error.response?.status)) ElMessage.error(error.message || '年度生产资料加载失败')
    try {
      plantingSchedule.value = await getFarmPlantingSchedule(selectedFarmId.value)
      form.templateVersionId = plantingSchedule.value.templateVersionId || ''
      form.plannedPlantingDate = plantingSchedule.value.plannedPlantingDate || ''
    } catch (scheduleError) { ElMessage.error(scheduleError.message || '定植安排加载失败') }
  }
}
async function loadResources() {
  loading.value = true
  try {
    const [farmRows, templateRows] = await Promise.all([listFarms(), listCropTemplates()])
    farms.value = farmRows
    templates.value = templateRows
    selectedFarmId.value = farms.value[0]?.id || ''
    await loadContext()
  } catch (error) { ElMessage.error(error.message || '农场资料加载失败') }
  finally { loading.value = false }
}
async function saveProfile() {
  if (!form.templateVersionId || !form.plannedPlantingDate) return ElMessage.warning('请选择生产模板并填写计划定植日期')
  saving.value = true
  try {
    await saveFarmPlantingSchedule(selectedFarmId.value, { templateVersionId: form.templateVersionId, plannedPlantingDate: form.plannedPlantingDate })
    setupOpen.value = false
    await loadContext()
    ElMessage.success('定植任务已下发；农户全部完成后将自动启用年度生产建议')
  } catch (error) { ElMessage.error(error.message || '生产资料保存失败') }
  finally { saving.value = false }
}
async function generatePlans() {
  try {
    await ElMessageBox.confirm(`将按${trackLabel.value}为全部在用地块生成本生产年度尚未到期的农事建议。已生成的计划会被替换。`, '生成年度农事建议', { type: 'warning', confirmButtonText: '生成', cancelButtonText: '取消' })
    generating.value = true
    const result = await generateFarmPlans(selectedFarmId.value, { regenerate: true })
    ElMessage.success(`已生成 ${result.taskCount} 项农事建议`)
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message || '生成失败')
  } finally { generating.value = false }
}
onMounted(loadResources)
</script>

<template>
  <div class="farmer-page annual-production-page">
    <div class="page-head">
      <div><h1 class="page-title">年度生产管理</h1><p class="page-subtitle">按脐橙物候期跟进全园管理，并将当前阶段建议下发给各地块。</p></div>
      <el-button type="primary" :loading="generating" :disabled="!context" @click="generatePlans"><el-icon><MagicStick /></el-icon>生成本年度建议</el-button>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else>
      <section class="farm-switcher"><span>当前农场</span><el-select v-model="selectedFarmId" size="large" @change="loadContext"><el-option v-for="farm in farms" :key="farm.id" :label="`${farm.name} · ${farm.city || ''}`" :value="farm.id" /></el-select><el-button v-if="!context" plain @click="setupOpen=true">安排定植</el-button></section>
      <el-alert v-if="!context && !plantingSchedule?.plannedPlantingDate" title="尚未安排定植" description="选择标准模板和计划定植日期后，系统会向各有效地块下发定植任务。" type="warning" :closable="false" show-icon />
      <section v-else-if="!context" class="content-panel planting-wait"><div><span>计划定植日期</span><strong>{{ plantingSchedule.plannedPlantingDate }}</strong><p>{{ plantingSchedule.templateName }} · V{{ plantingSchedule.versionNo }}，仍有 {{ plantingSchedule.pendingTaskCount }} 个地块定植任务待完成。</p></div><el-button plain @click="setupOpen=true">调整安排</el-button></section>
      <template v-else>
        <section class="production-hero">
          <div><span class="eyebrow">{{ context.productionYear }} 生产年度 · {{ context.productionYearStartsOn }} 至 {{ context.productionYearEndsOn }}</span><h2>{{ context.stage?.name || '当前无匹配物候期' }}</h2><p>{{ context.stage?.managementFocus || '等待生产模板配置当前阶段。' }}</p></div>
          <div class="hero-facts"><span><b>{{ trackLabel }}</b><small>全园统一轨道</small></span><span><b>{{ context.treeAgeYears }} 年</b><small>按实际定植日期计算</small></span></div>
        </section>
        <section class="content-panel orchard-facts">
          <div><span>果园实际定植日期</span><strong>{{ context.plantingDate }}</strong><small>农户完成全部定植任务后由系统确认</small></div>
          <div><span>生产模板</span><strong>{{ context.templateName }} · V{{ context.versionNo }}</strong><small>公司级标准模板</small></div>
          <div><span>当前土壤湿度建议</span><strong>{{ context.stage?.moistureMin ?? '-' }}% - {{ context.stage?.moistureMax ?? '-' }}%</strong><small>结合现场传感器、天气和树势调整</small></div>
        </section>
        <section class="annual-layout">
          <article class="content-panel suggestions"><div class="section-head"><div><h3>当前阶段建议</h3><p>建议日期可由农户依据现场情况调整。</p></div></div><el-empty v-if="!context.suggestions.length" :image-size="52" description="当前阶段暂无建议"/><ul v-else><li v-for="item in context.suggestions" :key="`${item.title}-${item.scheduledDate}`"><span>{{ item.scheduledDate }}</span><div><strong>{{ item.title }}</strong><p>{{ item.note || '请结合现场树势、土壤湿度和天气安排。' }}</p></div></li></ul></article>
          <article class="content-panel timeline"><div class="section-head"><div><h3>全年物候节奏</h3><p>生产年度固定为上年 12 月至当年 11 月。</p></div></div><ol><li v-for="stage in context.stages" :key="stage.code" :class="{ active: stage.code === currentStageCode }"><span>{{ stage.code }}</span><div><strong>{{ stage.name }}</strong><small>{{ dateRange(stage) }}</small></div></li></ol></article>
        </section>
      </template>
    </template>
    <el-dialog v-model="setupOpen" title="安排果园定植" width="min(520px, 92vw)"><el-form label-position="top"><el-form-item label="定植后采用的生产模板" required><el-select v-model="form.templateVersionId" placeholder="选择脐橙模板"><el-option v-for="item in templates" :key="item.versionId" :label="`${item.name} · V${item.versionNo}`" :value="item.versionId"/></el-select></el-form-item><el-form-item label="计划定植日期" required><el-date-picker v-model="form.plannedPlantingDate" type="date" value-format="YYYY-MM-DD" :disabled-date="(day) => day < new Date(new Date().setHours(0, 0, 0, 0))"/><small class="field-help">保存后将为每个有效地块创建“完成脐橙定植”任务。农户全部完成后，系统以任务完成日期写入果园实际定植日期。</small></el-form-item></el-form><template #footer><el-button @click="setupOpen=false">取消</el-button><el-button type="primary" :loading="saving" @click="saveProfile">下发定植任务</el-button></template></el-dialog>
  </div>
</template>

<style scoped>
.farm-switcher{display:flex;align-items:center;gap:12px;margin-bottom:18px;padding:13px 16px;border:1px solid #cee6d8;border-radius:8px;background:#f8fcf9;color:#557164}.farm-switcher>span,.eyebrow{color:#1f7a5b;font-size:12px;font-weight:700}.farm-switcher .el-select{width:300px}.planting-wait{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:18px}.planting-wait span,.planting-wait p{display:block;margin:0;color:#84938d;font-size:12px}.planting-wait strong{display:block;margin:6px 0;color:#315447;font-size:22px}.production-hero{display:flex;align-items:end;justify-content:space-between;gap:24px;margin-bottom:18px;padding:24px 26px;border-left:5px solid #e58226;background:#f6faf5}.production-hero h2{margin:8px 0;color:#254337;font-size:26px}.production-hero p{max-width:620px;margin:0;color:#60776d;line-height:1.7}.hero-facts{display:flex;gap:26px;white-space:nowrap}.hero-facts span{display:grid;gap:5px}.hero-facts b{color:#315447;font-size:19px}.hero-facts small,.orchard-facts span,.orchard-facts small,.field-help{color:#84938d;font-size:11px}.orchard-facts{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin-bottom:18px;padding:0;overflow:hidden}.orchard-facts>div{display:grid;gap:6px;padding:15px 18px;background:#fbfdfc}.orchard-facts strong{color:#315447;font-size:14px}.annual-layout{display:grid;grid-template-columns:1.25fr .75fr;gap:18px}.suggestions ul{display:grid;gap:2px;margin:0;padding:0;list-style:none}.suggestions li{display:grid;grid-template-columns:94px 1fr;gap:12px;padding:13px 0;border-bottom:1px solid #edf2ef}.suggestions li:last-child{border-bottom:0}.suggestions li>span{color:#b96d21;font-size:12px;font-weight:700}.suggestions li strong{color:#315447;font-size:14px}.suggestions li p{margin:5px 0 0;color:#70827b;font-size:12px;line-height:1.6}.timeline ol{display:grid;gap:4px;margin:0;padding:0;list-style:none}.timeline li{display:flex;gap:10px;padding:8px;color:#6f817a}.timeline li>span{width:28px;height:28px;display:grid;place-items:center;border:1px solid #dce9e3;border-radius:50%;font-size:10px}.timeline li div{display:grid;gap:2px}.timeline li strong{font-size:13px}.timeline li small{font-size:11px}.timeline li.active{padding:10px;border-left:3px solid #e58226;color:#28533f;background:#fff8ef}.timeline li.active>span{border-color:#e58226;color:#bd6921}@media(max-width:760px){.production-hero{align-items:flex-start;flex-direction:column}.hero-facts{gap:22px}.orchard-facts,.annual-layout{grid-template-columns:1fr}.farm-switcher{align-items:stretch;flex-direction:column}.farm-switcher .el-select{width:100%}.planting-wait{align-items:flex-start;flex-direction:column}}@media(max-width:440px){.hero-facts{width:100%;justify-content:space-between}.production-hero{padding:20px}.suggestions li{grid-template-columns:1fr}}
</style>
