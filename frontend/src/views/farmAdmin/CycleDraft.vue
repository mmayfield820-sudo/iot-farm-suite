<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createFarmCycleDraft, getFarmAnnualProduction, getFarmCycleDraft, listCropTemplates, listFarms, publishFarmCycleDraft, rebaseFarmCycleDraft, updateFarmCycleDraft } from '@/api/production'
import { usePlatformStore } from '@/stores/platform'
import yearPlanSpring from '@/assets/year-plan-spring.jpg'
import yearPlanAutumn from '@/assets/year-plan-autumn.jpg'

const router = useRouter()
const platformStore = usePlatformStore()
const farms = ref([])
const templates = ref([])
const selectedFarmId = ref('')
const current = ref(null)
const next = ref(null)
const draft = ref(null)
const loading = ref(false)
const saving = ref(false)
const publishing = ref(false)
const stageListRef = ref(null)
const form = reactive({ sourceType: 'current', sourceVersionId: '', extendYoungTrack: false, trackOverrideReason: '', changeNote: '' })

const nextYear = computed(() => (current.value?.productionYear || new Date().getFullYear()) + 1)
const initialSetup = computed(() => Boolean(current.value?.canCustomizeInitialTemplate))
const targetContext = computed(() => initialSetup.value ? current.value : next.value)
const targetYear = computed(() => initialSetup.value ? current.value?.productionYear : nextYear.value)
const autoTrack = computed(() => targetContext.value?.treeAgeYears <= 3 ? 'young' : 'fruiting')
const canExtendYoung = computed(() => targetContext.value?.treeAgeYears === 4 && autoTrack.value === 'fruiting')
const published = computed(() => !initialSetup.value && Boolean(next.value?.annualConfigured))
const stages = computed(() => draft.value?.versionDefinition?.stages || [])
const standardTemplateOptions = computed(() => templates.value)
const selectedFarm = computed(() => farms.value.find((farm) => String(farm.id) === String(selectedFarmId.value)))
const trackLabel = (track) => track === 'young' ? '幼树轨道' : '结果树轨道'

function resetExtension(value) {
  if (!value) form.trackOverrideReason = ''
}

function scrollToStages() {
  stageListRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function addTask(stage) {
  stage.tasks ||= []
  stage.tasks.push({ type: 'other', title: '', offsetDays: 0, suggestedTime: null, note: '', track: null, repeatDays: null, repeatUntilStageEnd: false })
}

function removeTask(stage, index) {
  stage.tasks.splice(index, 1)
}

function addStage() {
  stages.value.push({ code: `S${stages.value.length + 1}`, name: '新生长阶段', durationDays: 30, moistureMin: 55, moistureMax: 70, managementFocus: '', tasks: [] })
}

function removeStage(index) {
  stages.value.splice(index, 1)
}

function moveStage(index, offset) {
  const target = index + offset
  if (target < 0 || target >= stages.value.length) return
  const [stage] = stages.value.splice(index, 1)
  stages.value.splice(target, 0, stage)
}

function normalizeDefinition() {
  return {
    stages: stages.value.map((stage) => ({
      ...stage,
      durationDays: Number(stage.durationDays),
      moistureMin: stage.moistureMin === null || stage.moistureMin === '' ? null : Number(stage.moistureMin),
      moistureMax: stage.moistureMax === null || stage.moistureMax === '' ? null : Number(stage.moistureMax),
      tasks: (stage.tasks || []).map((task) => ({
        ...task,
        offsetDays: Number(task.offsetDays),
        repeatDays: task.repeatDays === null || task.repeatDays === '' ? null : Number(task.repeatDays),
        repeatUntilStageEnd: task.repeatDays !== null && task.repeatDays !== '',
      })),
    })),
  }
}

async function loadPlans() {
  current.value = null
  next.value = null
  draft.value = null
  if (!selectedFarmId.value) return
  try {
    current.value = await getFarmAnnualProduction(selectedFarmId.value)
    next.value = await getFarmAnnualProduction(selectedFarmId.value, { productionYear: current.value.productionYear + 1 })
    form.sourceType = initialSetup.value ? 'standard' : 'current'
    form.sourceVersionId = initialSetup.value ? (standardTemplateOptions.value[0]?.versionId || current.value.templateVersionId) : current.value.templateVersionId
    form.extendYoungTrack = targetContext.value.trackSource === 'extended_young'
    form.trackOverrideReason = targetContext.value.trackOverrideReason || ''
    try {
      draft.value = await getFarmCycleDraft(selectedFarmId.value)
      form.changeNote = draft.value.changeNote || ''
    } catch (error) {
      if (error.response?.status !== 404) throw error
      form.changeNote = ''
    }
  } catch (error) { ElMessage.error(error.message || '下一生产年度资料加载失败') }
}

async function loadResources() {
  loading.value = true
  try {
    const [farmRows, templateRows] = await Promise.all([listFarms(), listCropTemplates({ includeAllVersions: true })])
    farms.value = farmRows
    templates.value = templateRows
    selectedFarmId.value = farms.value.some((farm) => String(farm.id) === String(platformStore.selectedFarmId)) ? String(platformStore.selectedFarmId) : farms.value[0]?.id || ''
    if (selectedFarmId.value !== String(platformStore.selectedFarmId || '')) platformStore.selectFarm(selectedFarmId.value)
    await loadPlans()
  } catch (error) { ElMessage.error(error.message || '农场资料加载失败') }
  finally { loading.value = false }
}

async function createDraft() {
  if (form.sourceType === 'standard' && !form.sourceVersionId) return ElMessage.warning('请选择一个已发布标准模板')
  saving.value = true
  try {
    const sourceVersionId = form.sourceType === 'current' ? current.value.templateVersionId : form.sourceVersionId
    const sourceTemplateId = form.sourceType === 'current'
      ? current.value.templateId
      : standardTemplateOptions.value.find((item) => item.versionId === sourceVersionId)?.id
    if (!sourceTemplateId) return ElMessage.warning('请选择有效的已发布标准模板')
    draft.value = await createFarmCycleDraft(sourceTemplateId, selectedFarmId.value, { sourceVersionId, changeNote: form.changeNote.trim() || null })
    ElMessage.success(initialSetup.value ? '本农场首年管理计划草稿已创建' : '下一年度管理计划草稿已创建')
  } catch (error) { ElMessage.error(error.message || '草稿创建失败') }
  finally { saving.value = false }
}

async function rebaseDraft() {
  const sourceVersionId = form.sourceType === 'current' ? current.value.templateVersionId : form.sourceVersionId
  if (!sourceVersionId) return ElMessage.warning('请选择计划来源')
  try {
    await ElMessageBox.confirm('重新生成会覆盖当前草稿中的阶段和任务编辑，但不会影响已保存的年度计划、已下发任务和执行记录。', '确认重新选择计划来源', { type: 'warning', confirmButtonText: '确认重新生成', cancelButtonText: '取消' })
    saving.value = true
    draft.value = await rebaseFarmCycleDraft(draft.value.id, { sourceVersionId, changeNote: form.changeNote.trim() || null })
    ElMessage.success(form.sourceType === 'current' ? `已按 ${current.value.productionYear} 年度计划重新生成草稿` : '已按所选标准模板重新生成草稿')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message || '草稿重新生成失败')
  } finally { saving.value = false }
}

async function saveDraft(showSuccess = true) {
  if (!draft.value) return false
  if (stages.value.some((stage) => !stage.name?.trim() || Number(stage.durationDays) <= 0)) {
    ElMessage.warning('请完整填写阶段名称和持续天数')
    return false
  }
  if (stages.value.some((stage) => (stage.tasks || []).some((task) => !task.title?.trim()))) {
    ElMessage.warning('请填写所有农事任务名称')
    return false
  }
  saving.value = true
  try {
    draft.value = await updateFarmCycleDraft(draft.value.id, { versionDefinition: normalizeDefinition(), changeNote: form.changeNote.trim() || null })
    if (showSuccess) ElMessage.success(initialSetup.value ? '本农场首年管理计划草稿已保存' : '下一年度管理计划草稿已保存')
    return true
  } catch (error) {
    ElMessage.error(error.message || '草稿保存失败')
    return false
  } finally { saving.value = false }
}

async function publishDraft() {
  if (form.extendYoungTrack && !form.trackOverrideReason.trim()) return ElMessage.warning('请说明继续采用幼树轨道的原因')
  if (!await saveDraft(false)) return
  const publishingInitialTemplate = initialSetup.value
  try {
    await ElMessageBox.confirm(`保存后将作为 ${targetYear.value} 生产年度的本农场管理计划，并采用${trackLabel(form.extendYoungTrack ? 'young' : autoTrack.value)}。`, publishingInitialTemplate ? '保存本农场首年管理计划' : '保存下一年度管理计划', { type: 'warning', confirmButtonText: '确认保存', cancelButtonText: '取消' })
    publishing.value = true
    await publishFarmCycleDraft(draft.value.id, { productionYear: targetYear.value, extendYoungTrack: form.extendYoungTrack, trackOverrideReason: form.extendYoungTrack ? form.trackOverrideReason.trim() : null })
    ElMessage.success(`${targetYear.value} 生产年度本农场管理计划已保存`)
    if (publishingInitialTemplate) await router.push('/farm/production')
    else await loadPlans()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.message || '管理计划保存失败')
  } finally { publishing.value = false }
}

onMounted(loadResources)
watch(() => platformStore.selectedFarmId, async (farmId) => {
  const id = String(farmId || '')
  if (!id || id === String(selectedFarmId.value) || !farms.value.some((farm) => String(farm.id) === id)) return
  selectedFarmId.value = id
  await loadPlans()
})
</script>

<template>
  <div class="farmer-page annual-draft-page">
    <div class="page-head"><div><h1 class="page-title">{{ initialSetup ? '首次管理计划定制' : '下一年度管理计划' }}</h1><p class="page-subtitle">{{ initialSetup ? '选择公司级标准模板并按本农场实际调整，保存后可下发首年任务。' : '沿用本农场计划或选择标准模板，调整后保存为下一生产年度的独立管理计划。' }}</p></div><div v-if="draft" class="page-actions"><el-button :loading="saving" @click="saveDraft()">保存草稿</el-button><el-button type="primary" :loading="publishing" @click="publishDraft">保存管理计划</el-button></div></div>
    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else>
      <section class="farm-switcher"><div class="farm-display"><el-icon class="farm-display-icon"><House /></el-icon><strong>当前农场</strong><span>{{ selectedFarm?.name || '暂无可用农场' }}<template v-if="selectedFarm?.city"> · {{ selectedFarm.city }}</template></span></div></section>
      <el-alert v-if="!current || !next" title="尚不能维护下一年度管理计划" description="需要先完成果园定植并选择已发布的标准模板。" type="warning" :closable="false" show-icon />
      <template v-else>
        <section class="content-panel year-bridge">
          <img class="year-landscape year-landscape--spring" :src="yearPlanSpring" alt="" aria-hidden="true">
          <div class="year-copy year-copy--current">
            <span>{{ initialSetup ? '采用的标准模板' : '当前年度' }}</span>
            <strong>{{ initialSetup ? `V${current.versionNo}` : current.productionYear }}</strong>
            <small>{{ current.templateName }} · V{{ current.versionNo }}</small>
          </div>
          <el-icon class="year-arrow"><Right /></el-icon>
          <div class="year-copy year-copy--next">
            <span>{{ initialSetup ? '本农场首年计划' : '下一年度' }}</span>
            <strong>{{ initialSetup ? current.productionYear : nextYear }}</strong>
            <small>{{ published ? `${next.templateName} · V${next.versionNo}（已保存）` : '等待创建管理计划' }}</small>
          </div>
          <img class="year-landscape year-landscape--autumn" :src="yearPlanAutumn" alt="" aria-hidden="true">
        </section>

        <el-alert v-if="published && !draft" :title="`${nextYear} 生产年度管理计划已保存`" :description="`采用${trackLabel(next.track)}；后续标准模板更新不会改变这份农场计划。`" type="success" :closable="false" show-icon />

        <section v-if="!draft && !published" class="content-panel draft-empty">
          <div class="draft-source"><div><h3>{{ initialSetup ? '创建本农场首年管理计划草稿' : `创建 ${nextYear} 年度管理计划` }}</h3><p>手动选择计划来源，生成后仍可按本农场实际情况修改阶段和任务。</p></div>
            <el-radio-group v-model="form.sourceType" :disabled="initialSetup"><el-radio value="current">复制上一年度计划（{{ current.productionYear }} 年）</el-radio><el-radio value="standard">采用已发布标准模板</el-radio></el-radio-group>
            <small v-if="form.sourceType === 'current'" class="source-help">将完整复制 {{ current.productionYear }} 年本农场已保存的阶段、任务及轨道配置，不复制执行记录。</small>
            <el-select v-if="form.sourceType === 'standard'" v-model="form.sourceVersionId" filterable placeholder="选择标准模板版本"><el-option v-for="item in standardTemplateOptions" :key="item.versionId" :label="`${item.name} · V${item.versionNo}`" :value="item.versionId"/></el-select>
          </div>
          <el-button type="primary" :loading="saving" @click="createDraft"><el-icon><DocumentAdd /></el-icon>创建草稿</el-button>
        </section>

        <template v-if="draft">
          <section class="content-panel existing-draft-source">
            <div><h3>计划来源</h3><p>当前已有草稿。需要更换起点时，可重新选择来源并生成；现有草稿编辑内容将被覆盖。</p></div>
            <div class="source-controls"><el-radio-group v-model="form.sourceType" :disabled="initialSetup"><el-radio value="current">复制上一年度计划（{{ current.productionYear }} 年）</el-radio><el-radio value="standard">采用已发布标准模板</el-radio></el-radio-group><el-select v-if="form.sourceType === 'standard'" v-model="form.sourceVersionId" filterable placeholder="选择标准模板版本"><el-option v-for="item in standardTemplateOptions" :key="item.versionId" :label="`${item.name} · V${item.versionNo}`" :value="item.versionId"/></el-select></div>
            <el-button :loading="saving" @click="rebaseDraft">按此来源重新生成</el-button>
          </section>
          <section class="draft-layout">
            <article class="content-panel recommendation">
              <header class="track-card-head">
                <h3>年度轨道（{{ initialSetup ? '首个生产年度' : '下一年度' }}）</h3>
                <el-button plain @click="scrollToStages"><el-icon><EditPen /></el-icon>调整阶段</el-button>
              </header>
              <div class="track-recommendation">
                <span class="track-leaf" aria-hidden="true"></span>
                <div>
                  <div class="track-recommendation-title">
                    <strong>{{ trackLabel(form.extendYoungTrack ? 'young' : autoTrack) }}</strong>
                    <el-tag type="success" effect="light" round>{{ form.extendYoungTrack ? '人工调整' : '系统推荐' }}</el-tag>
                  </div>
                  <p>{{ initialSetup ? '首个生产年度' : '下一年度' }}树龄 {{ targetContext.treeAgeYears }} 年，{{ form.extendYoungTrack ? '已选择继续采用幼树轨道。' : `系统根据树龄自动推荐${trackLabel(autoTrack)}。` }}</p>
                </div>
              </div>
              <div v-if="canExtendYoung" class="track-decision">
                <el-switch v-model="form.extendYoungTrack" active-text="继续幼树轨道一年" inactive-text="采用系统推荐" @change="resetExtension"/>
                <el-input v-if="form.extendYoungTrack" v-model="form.trackOverrideReason" class="reason-input" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="填写延续幼树轨道的原因"/>
              </div>
              <div class="track-stage-flow">
                <div v-for="(stage, stageIndex) in stages" :key="stage.code || stageIndex" class="track-stage-card">
                  <strong>{{ stage.name || `阶段 ${stageIndex + 1}` }}</strong>
                  <i aria-hidden="true"></i>
                  <span>{{ stage.durationDays || '-' }} 天</span>
                </div>
              </div>
              <p class="track-footnote">阶段名称和时长为参考值，可根据本园实际情况调整。</p>
            </article>
            <article class="content-panel change-note"><div class="section-head"><div><h3>调整说明</h3><p>记录本农场相对当前版本的调整依据。</p></div></div><el-input v-model="form.changeNote" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="例如：结合本园树势和上一年度执行情况调整任务频次"/></article>
          </section>

          <section ref="stageListRef" class="content-panel stage-list">
            <header class="stage-list-head"><div><h2>下一年度管理计划</h2><p>设置下一年度各生长阶段、持续天数、土壤湿度目标和农事任务。</p></div></header>
            <article v-for="(stage, stageIndex) in stages" :key="stageIndex" class="stage-editor">
              <header><div class="stage-title"><el-input v-model="stage.code" aria-label="阶段编号"/><el-input v-model="stage.name" aria-label="阶段名称"/></div><div class="stage-actions"><el-button circle text title="上移阶段" :disabled="stageIndex === 0" @click="moveStage(stageIndex, -1)"><el-icon><ArrowUp /></el-icon></el-button><el-button circle text title="下移阶段" :disabled="stageIndex === stages.length - 1" @click="moveStage(stageIndex, 1)"><el-icon><ArrowDown /></el-icon></el-button><el-button link type="primary" @click="addTask(stage)"><el-icon><Plus /></el-icon>添加任务</el-button><el-button link type="danger" :disabled="stages.length === 1" @click="removeStage(stageIndex)"><el-icon><Delete /></el-icon>删除阶段</el-button></div></header>
              <el-form class="stage-fields" label-position="top"><el-form-item label="阶段天数"><el-input-number v-model="stage.durationDays" :min="1" :max="366" controls-position="right"/></el-form-item><el-form-item label="土壤湿度下限（%）"><el-input-number v-model="stage.moistureMin" :min="0" :max="100" controls-position="right"/></el-form-item><el-form-item label="土壤湿度上限（%）"><el-input-number v-model="stage.moistureMax" :min="0" :max="100" controls-position="right"/></el-form-item><el-form-item label="管理重点"><el-input v-model="stage.managementFocus"/></el-form-item></el-form>
              <div v-if="stage.tasks?.length" class="task-columns"><span>适用轨道</span><span>农事任务</span><span>阶段第几天</span><span>执行频次</span><span>执行说明</span><span></span></div>
              <div v-for="(task, index) in stage.tasks" :key="index" class="task-row">
                <div class="task-field"><span>适用轨道</span><el-select v-model="task.track"><el-option label="通用" :value="null"/><el-option label="幼树" value="young"/><el-option label="结果树" value="fruiting"/></el-select></div>
                <div class="task-field"><span>农事任务</span><el-input v-model="task.title" placeholder="任务名称"/></div>
                <div class="task-field"><span>阶段第几天</span><el-input-number v-model="task.offsetDays" :min="0" :max="Math.max(0, stage.durationDays - 1)" controls-position="right"/></div>
                <div class="task-field"><span>执行频次</span><el-select v-model="task.repeatDays" placeholder="仅一次"><el-option label="仅执行一次" :value="null"/><el-option label="每 7 天" :value="7"/><el-option label="每 14 天" :value="14"/><el-option label="每 30 天" :value="30"/></el-select></div>
                <div class="task-field"><span>执行说明</span><el-input v-model="task.note" placeholder="现场执行说明"/></div>
                <el-button circle text type="danger" title="删除任务" @click="removeTask(stage, index)"><el-icon><Delete /></el-icon></el-button>
              </div>
              <el-empty v-if="!stage.tasks?.length" :image-size="42" description="本阶段暂无任务"/>
            </article>
            <el-button class="add-stage" plain type="primary" @click="addStage"><el-icon><Plus /></el-icon>添加生长阶段</el-button>
          </section>
        </template>
      </template>
    </template>
  </div>
</template>

<style scoped>
.farm-switcher{display:flex;align-items:center;gap:12px;margin-bottom:18px;padding:13px 16px;border:1px solid #cee6d8;border-radius:8px;background:#f8fcf9;color:#557164}.farm-switcher>span{color:#1f7a5b;font-size:12px;font-weight:700}.farm-switcher .el-select{width:300px}.year-bridge{display:flex;align-items:center;justify-content:center;gap:28px;margin-bottom:18px}.year-bridge>div{display:grid;gap:5px;min-width:190px}.year-bridge span,.year-bridge small{color:#84938d;font-size:11px}.year-bridge strong{color:#315447;font-size:25px}.year-bridge .el-icon{color:#e58226;font-size:23px}.draft-empty,.existing-draft-source{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:18px}.draft-empty h3,.draft-empty p,.existing-draft-source h3,.existing-draft-source p{margin:0}.draft-empty p,.existing-draft-source p{margin-top:7px;color:#71827b;font-size:12px}.draft-source{display:grid;gap:14px;min-width:min(560px,100%)}.draft-source .el-select{width:min(420px,100%)}.source-help{color:#71827b;font-size:12px;line-height:1.6}.source-controls{min-width:min(470px,100%);display:grid;gap:10px}.source-controls .el-select{width:100%}.draft-layout{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(340px,.95fr);gap:18px;margin:18px 0}.reason-input{margin-top:15px}.stage-list{display:block;scroll-margin-top:20px}.stage-list-head{padding-bottom:16px;border-bottom:1px solid #e5ece8}.stage-list-head h2,.stage-list-head p{margin:0}.stage-list-head h2{color:#193f33;font-size:20px;line-height:1.35}.stage-list-head p{margin-top:6px;color:#7b8c85;font-size:12px;line-height:1.55}.stage-editor{padding:18px 0;border-bottom:1px solid #edf2ef}.stage-editor header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}.stage-editor header>div{display:grid;grid-template-columns:48px minmax(180px,320px);align-items:center;gap:8px}.stage-editor header strong{color:#1f7a5b}.stage-fields{display:grid;grid-template-columns:130px 140px 140px minmax(220px,1fr);gap:10px}.stage-fields :deep(.el-form-item){margin-bottom:12px}.stage-fields :deep(.el-input-number){width:100%}.task-columns,.task-row{display:grid;grid-template-columns:110px minmax(150px,1fr) 110px 120px minmax(190px,1.3fr) 32px;gap:8px}.task-columns{padding:0 2px;color:#829089;font-size:11px}.task-row{margin-top:8px}@media(max-width:1100px){.draft-layout{grid-template-columns:1fr}}@media(max-width:900px){.stage-fields{grid-template-columns:1fr 1fr}.task-columns{display:none}.task-row{grid-template-columns:1fr 1fr}.task-row>.el-button{justify-self:end}.existing-draft-source{align-items:flex-start;flex-direction:column}.source-controls{min-width:0;width:100%}}@media(max-width:600px){.farm-switcher{align-items:stretch;flex-direction:column}.farm-switcher .el-select{width:100%}.year-bridge{justify-content:space-between;gap:10px}.year-bridge>div{min-width:0}.draft-empty{align-items:flex-start;flex-direction:column}.draft-source{min-width:0}.draft-source .el-radio-group,.source-controls .el-radio-group{align-items:flex-start;flex-direction:column}.stage-fields,.task-row{grid-template-columns:1fr}.stage-editor header{align-items:flex-start;flex-direction:column}.stage-editor header>div{width:100%;grid-template-columns:42px 1fr}}
.stage-editor header>.stage-title{display:grid;width:auto;grid-template-columns:68px minmax(180px,320px)}.stage-editor header>.stage-actions{display:flex;width:auto;grid-template-columns:none;flex-wrap:wrap}.add-stage{width:100%;margin-top:14px}@media(max-width:900px){.stage-editor header{align-items:flex-start;flex-direction:column}.stage-editor header>.stage-actions{width:100%}}@media(max-width:600px){.stage-editor header>.stage-title{width:100%;grid-template-columns:64px 1fr}}
.stage-fields{grid-template-columns:minmax(110px,.65fr) minmax(130px,.75fr) minmax(130px,.75fr) minmax(240px,1.8fr)}.stage-fields :deep(.el-form-item){min-width:0}.stage-fields :deep(.el-form-item__label){height:auto;min-height:20px;padding:0 0 5px;line-height:1.35}.task-row{align-items:end;gap:10px}.task-field{display:grid;min-width:0}.task-field>span{display:none;color:#71827b;font-size:11px;line-height:1.35}.task-field :deep(.el-input-number),.task-field :deep(.el-select){width:100%}@media(max-width:1500px){.stage-fields{grid-template-columns:repeat(2,minmax(0,1fr))}.task-columns{display:none}.task-row{grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:12px;border:1px solid #edf2ef;border-radius:8px;background:#fcfefd}.task-field{gap:5px}.task-field>span{display:block}.task-row>.el-button{justify-self:end}}@media(max-width:760px){.stage-fields,.task-row{grid-template-columns:1fr}.task-row>.el-button{margin-top:2px}}

.recommendation{padding:18px 22px}
.track-card-head{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:12px}
.track-card-head h3{margin:0;color:#193f33;font-size:18px;line-height:1.3}
.track-card-head :deep(.el-button){height:34px;padding:0 15px;color:#536d63;border-color:#d8e2dd;background:#fff;font-size:12px}
.track-recommendation{display:flex;align-items:center;gap:14px;padding:13px 16px;border:1px solid #dceddf;border-radius:8px;background:#f1f8f2}
.track-recommendation>div{min-width:0}
.track-leaf{position:relative;width:46px;height:46px;flex:0 0 46px}
.track-leaf::before{position:absolute;top:3px;left:6px;width:33px;height:29px;border-radius:80% 18% 75% 18%;background:#9ad46f;box-shadow:inset -5px -4px 0 rgba(79,154,75,.12);content:"";transform:rotate(-12deg)}
.track-leaf::after{position:absolute;left:7px;bottom:7px;width:39px;height:3px;border-radius:4px;background:#6fb356;content:"";transform:rotate(-55deg);transform-origin:left center}
.track-recommendation-title{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.track-recommendation-title strong{color:#123d31;font-size:20px;line-height:1.2}
.track-recommendation-title :deep(.el-tag){height:25px;padding:0 10px;border-color:#d3ebd1;color:#31895f;background:#e7f5e6;font-size:11px;font-weight:700}
.track-recommendation p{margin:6px 0 0;color:#71847b;font-size:12px;line-height:1.45}
.track-decision{margin-top:10px;padding:10px 14px;border-left:3px solid #8cc49b;background:#f7faf8}
.track-decision .reason-input{max-width:720px}
.track-stage-flow{display:flex;gap:14px;margin-top:12px;padding:0 1px 5px;overflow-x:auto;scrollbar-width:thin;scrollbar-color:#c8dbd1 transparent}
.track-stage-card{position:relative;display:flex;min-width:94px;min-height:80px;flex:1 0 94px;align-items:center;flex-direction:column;justify-content:center;padding:9px 7px;border:1px solid #dfe7e3;border-radius:8px;background:#fff;text-align:center}
.track-stage-card::after{position:absolute;top:50%;right:-12px;color:#93bbaa;font-size:22px;font-weight:300;line-height:1;content:"›";transform:translateY(-54%)}
.track-stage-card:last-child::after{display:none}
.track-stage-card strong{color:#314b42;font-size:11px;line-height:1.35}
.track-stage-card i{width:6px;height:6px;margin:8px 0;border-radius:50%;background:#24a35f;box-shadow:0 0 0 3px #eef8f2}
.track-stage-card span{color:#263e36;font-size:16px;line-height:1}
.track-footnote{margin:10px 0 0;color:#7c8984;font-size:11px;line-height:1.45}
.change-note{display:flex;min-width:0;flex-direction:column}
.change-note :deep(.el-textarea){display:flex;min-height:140px;flex:1}
.change-note :deep(.el-textarea__inner){height:100%;resize:none}
@media(max-width:760px){
  .recommendation{padding:16px}
  .track-card-head h3{font-size:17px}
  .track-recommendation{align-items:flex-start}
  .track-stage-card{min-width:104px;min-height:80px;flex-basis:104px}
  .change-note :deep(.el-textarea){min-height:130px}
}

.year-bridge{
  position:relative;
  display:grid;
  grid-template-columns:minmax(0,1fr) 76px minmax(0,1fr);
  min-height:210px;
  margin-bottom:18px;
  padding:34px 12%;
  overflow:hidden;
  border-color:#dfe7e3;
  background:#fff;
  box-shadow:0 3px 14px rgba(42,77,64,.05);
  isolation:isolate;
}
.year-bridge>.year-copy{
  z-index:2;
  display:flex;
  min-width:0;
  align-items:center;
  flex-direction:column;
  justify-content:center;
  text-align:center;
}
.year-copy span{
  padding:6px 16px;
  border-radius:999px;
  color:#23835f;
  background:#e8f5ec;
  font-size:16px;
  font-weight:700;
  line-height:1.25;
}
.year-copy--next span{color:#ef8a24;background:#fff2df}
.year-copy strong{
  margin-top:17px;
  color:#075c45;
  font-size:48px;
  font-weight:700;
  line-height:1;
}
.year-copy small{
  margin-top:22px;
  color:#334d44;
  font-size:16px;
  line-height:1.45;
}
.year-bridge>.year-arrow{z-index:2;align-self:center;color:#f28a19;font-size:45px}
.year-bridge>.year-landscape{position:absolute;z-index:0;bottom:0;display:block;width:38%;min-width:0;height:100%;object-fit:contain;pointer-events:none}
.year-landscape--spring{left:0;object-position:left center}
.year-landscape--autumn{right:0;object-position:right center}
.farm-switcher{min-height:58px;justify-content:space-between;padding:13px 18px;border-color:#dfe7e3;background:#fff}
.farm-display{display:flex;min-width:0;align-items:center;gap:13px}
.farm-display-icon{flex:0 0 auto;color:#18835c;font-size:24px}
.farm-display strong{flex:0 0 auto;color:#263e36;font-size:14px}
.farm-display>span:last-child{overflow:hidden;color:#4f675e;font-size:14px;text-overflow:ellipsis;white-space:nowrap}
@media(max-width:900px){
  .year-bridge{min-height:184px;padding:28px 5%}
  .year-copy strong{font-size:40px}
  .year-copy small{margin-top:18px;font-size:14px}
  .year-bridge>.year-landscape{width:36%;opacity:.82}
}
@media(max-width:600px){
  .year-bridge{grid-template-columns:minmax(0,1fr) 34px minmax(0,1fr);min-height:164px;padding:22px 10px}
  .year-copy span{padding:5px 9px;font-size:12px}
  .year-copy strong{margin-top:14px;font-size:32px}
  .year-copy small{margin-top:16px;font-size:11px}
  .year-bridge>.year-arrow{font-size:28px}
  .year-bridge>.year-landscape{width:43%;opacity:.62}
  .farm-display{width:100%;gap:10px}
  .farm-display>span:last-child{white-space:normal}
}
</style>
