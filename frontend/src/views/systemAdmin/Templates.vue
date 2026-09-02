<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createCropTemplate, createCropTemplateVersion, getCropTemplateVersion, listCropTemplates } from '@/api/production'

const templates = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingTemplateId = ref('')
const keyword = ref('')
const stages = [
  ['S1', '休眠期（清园越冬）', '12 月 - 次年 1 月', 62, 55, 65, '清园越冬、修剪和防冻'],
  ['S2', '春梢萌动期', '2 月 - 3 月', 59, 60, 70, '促梢、整形和春季病虫害防治'],
  ['S3', '花期', '4 月', 30, 60, 70, '幼树养树，结果树保花保果'],
  ['S4', '稳果期', '5 月 - 6 月', 61, 65, 75, '控夏梢、稳果和病虫害防治'],
  ['S5', '果实膨大期', '7 月 - 8 月', 62, 65, 75, '抗旱、稳水稳肥和秋梢管理'],
  ['S6', '转色期', '9 月 - 10 月', 61, 55, 70, '控晚秋梢，促进果实转色'],
  ['S7', '采收期', '11 月', 30, 55, 65, '适时采收和采后清园准备'],
]
function task(type, title, note, track = null, offsetDays = 7, repeatDays = null) { return { type, title, offsetDays, suggestedTime: null, note, track, repeatDays, repeatUntilStageEnd: repeatDays !== null } }
const defaultTaskSets = {
  S1: [
    task('pruning', '冬季修剪与清园', '结合树势修剪，清除病虫枝、落叶和园内病残体。', null, 2),
    task('fertilization', '冬肥与树势检查', '结合土壤和树势核对冬肥安排，避免一次性过量施用。', null, 14),
    task('inspection', '越冬防冻与设备巡检', '检查树干防冻、排水设施和灌溉设备状态。', null, 28, 14),
  ],
  S2: [
    task('inspection', '春梢萌芽与树势巡查', '记录新梢长度、萌芽整齐度和病虫害情况。', null, 0, 14),
    task('irrigation', '春季土壤湿度检查', '结合天气和传感器数据判断是否需要补水。', null, 7, 7),
    task('fertilization', '催芽肥检查', '根据树势和土壤条件核对春季施肥安排。', null, 14),
    task('pruning', '春季整形修剪检查', '幼树培养树形，结果树疏除交叉枝和弱枝。', null, 21, 14),
    task('flower_management', '疏除花蕾', '幼树不留花果，减少养分消耗。', 'young', 28, 7),
  ],
  S3: [
    task('inspection', '花期与坐果巡查', '记录开花、坐果和异常落花情况。', null, 0, 7),
    task('flower_management', '摘除幼果', '幼树不留果，保持营养生长。', 'young', 5, 7),
    task('flower_management', '保花保果巡查', '结合花量、树势和天气决定措施。', 'fruiting', 10, 7),
    task('pest_control', '花期病虫害巡查', '重点检查蓟马、红蜘蛛等风险并记录。', null, 20, 7),
  ],
  S4: [
    task('pruning', '夏梢生长检查', '幼树短截抹梢；结果树重点控制旺长夏梢。', null, 0, 14),
    task('fruit_management', '第一次疏果', '去除小果、病虫果和畸形果。', 'fruiting', 15),
    task('pest_control', '稳果期病虫害巡查', '结合叶片、幼果和天气检查病虫害风险。', null, 30, 14),
  ],
  S5: [
    task('irrigation', '果实膨大期土壤湿度检查', '高温伏旱期结合天气和传感器数据安排灌溉或覆盖。', null, 0, 7),
    task('inspection', '果实膨大情况巡查', '记录果径、树势和异常落果情况。', 'fruiting', 14, 14),
    task('pruning', '秋梢生长检查', '检查秋梢整齐度，及时处理过密枝和徒长枝。', null, 28, 14),
    task('fruit_management', '第二次疏果', '按叶果比和树势调整结果负载。', 'fruiting', 45),
  ],
  S6: [
    task('pruning', '抹除晚秋梢', '关注 9 月中旬后抽生的新梢。', 'young', 0, 7),
    task('inspection', '转色与成熟度巡查', '结果树关注果实转色、成熟度和病虫害。', 'fruiting', 0, 7),
    task('irrigation', '成熟期土壤湿度检查', '结合天气和树势适度控水，避免持续干旱。', null, 14, 7),
    task('harvest', '采收准备检查', '核对成熟度、天气、采收工具和人员安排。', 'fruiting', 35),
  ],
  S7: [
    task('harvest', '成熟度检查', '果实完全转黄、糖酸比适宜时安排采收。', 'fruiting', 0, 7),
    task('harvest', '采收条件检查', '结合天气、果面状态和储运安排确认采收窗口。', 'fruiting', 7, 7),
    task('cleanup', '采后清园', '清除落果、枯枝和园内废弃物，降低越冬病虫基数。', null, 14),
    task('inspection', '采后果园与设备巡检', '检查树势恢复、排水和灌溉设备状态。', null, 21),
  ],
}
function defaultStages() {
  return stages.map(([code, name, period, durationDays, moistureMin, moistureMax, managementFocus]) => ({ code, name, period, durationDays, moistureMin, moistureMax, managementFocus, tasks: (defaultTaskSets[code] || []).map((item) => ({ ...item })) }))
}
const form = reactive({ name: '奉节脐橙全生命周期周年管理总模板', crop: '脐橙', province: '重庆市', city: '奉节县', changeNote: '', stages: defaultStages() })
const filteredTemplates = computed(() => templates.value.filter((item) => `${item.name}${item.crop}${item.province || ''}${item.city || ''}`.toLowerCase().includes(keyword.value.toLowerCase())))
function resetForm() { Object.assign(form, { name: '奉节脐橙全生命周期周年管理总模板', crop: '脐橙', province: '重庆市', city: '奉节县', changeNote: '', stages: defaultStages() }) }
function openCreate() { editingTemplateId.value = ''; resetForm(); dialogVisible.value = true }
async function openVersion(item) {
  saving.value = true
  try {
    const detail = await getCropTemplateVersion(item.versionId)
    editingTemplateId.value = item.id
    Object.assign(form, { name: detail.name, crop: detail.crop, province: detail.province || '', city: detail.city || '', changeNote: '', stages: detail.versionDefinition.stages.map((stage) => ({ ...stage, tasks: (stage.tasks || []).map((entry) => ({ ...entry })) })) })
    dialogVisible.value = true
  } catch (error) { ElMessage.error(error.message || '模板版本加载失败') }
  finally { saving.value = false }
}
function addTask(stage) { stage.tasks.push(task('inspection', '巡园检查', '结合树势、土壤湿度和天气安排。')) }
function removeTask(stage, index) { stage.tasks.splice(index, 1) }
function addStage() { form.stages.push({ code: `S${form.stages.length + 1}`, name: '新生长阶段', durationDays: 30, moistureMin: 55, moistureMax: 70, managementFocus: '', tasks: [] }) }
function removeStage(index) { form.stages.splice(index, 1) }
async function loadTemplates() { loading.value = true; try { templates.value = await listCropTemplates() } catch (error) { ElMessage.error(error.message || '模板列表加载失败') } finally { loading.value = false } }
function normalizedDefinition() {
  if (!form.stages.length) throw new Error('模板至少需要一个生长阶段')
  return { stages: form.stages.map((stage) => {
    if (!stage.code?.trim() || !stage.name?.trim() || Number(stage.durationDays) <= 0) throw new Error('请完整填写阶段编号、名称和天数')
    if (stage.moistureMin !== null && stage.moistureMax !== null && Number(stage.moistureMin) > Number(stage.moistureMax)) throw new Error(`${stage.name}的土壤湿度下限不能高于上限`)
    return { code: stage.code.trim(), name: stage.name.trim(), durationDays: Number(stage.durationDays), moistureMin: stage.moistureMin === null ? null : Number(stage.moistureMin), moistureMax: stage.moistureMax === null ? null : Number(stage.moistureMax), managementFocus: stage.managementFocus?.trim() || null, tasks: stage.tasks.map((entry) => {
    if (!entry.type.trim() || !entry.title.trim()) throw new Error(`${stage.name} 中存在未填写完整的建议`)
    return { type: entry.type.trim(), title: entry.title.trim(), offsetDays: Number(entry.offsetDays ?? 0), suggestedTime: null, note: entry.note?.trim() || null, track: entry.track || null, repeatDays: entry.repeatDays ? Number(entry.repeatDays) : null, repeatUntilStageEnd: Boolean(entry.repeatDays) }
  }) }
  }) }
}
async function submit() { saving.value = true; try { const versionDefinition = normalizedDefinition(); if (editingTemplateId.value) await createCropTemplateVersion(editingTemplateId.value, { versionDefinition, changeNote: form.changeNote.trim() || null }); else await createCropTemplate({ name: form.name.trim(), crop: form.crop.trim(), province: form.province.trim() || null, city: form.city.trim() || null, versionDefinition }); ElMessage.success(editingTemplateId.value ? '标准模板新版本已发布' : '周年管理模板已发布'); dialogVisible.value = false; await loadTemplates() } catch (error) { ElMessage.error(error.message || '模板发布失败') } finally { saving.value = false } }
onMounted(loadTemplates)
</script>

<template>
  <div class="farmer-page templates-page">
    <div class="page-head"><div><h1 class="page-title">脐橙周年管理模板</h1><p class="page-subtitle">按固定物候期维护建议；具体执行由天气、土壤湿度和田间生长信号共同决定。</p></div><el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon>新建周年模板</el-button></div>
    <section class="content-panel template-library"><div class="toolbar"><el-input v-model="keyword" clearable placeholder="搜索模板、品种或地区"><template #prefix><el-icon><Search /></el-icon></template></el-input><span>当前已发布 {{ filteredTemplates.length }} 个标准模板</span></div><el-skeleton v-if="loading" :rows="5" animated/><el-empty v-else-if="!filteredTemplates.length" :image-size="74" description="暂无已发布的标准模板"/><div v-else class="template-grid"><article v-for="item in filteredTemplates" :key="item.versionId" class="template-card"><span>{{ item.crop }} · V{{ item.versionNo }}</span><h2>{{ item.name }}</h2><p>{{ item.province || '通用地区' }} {{ item.city || '' }}</p><small>已发布版本保持只读，新调整通过新版本发布。</small><el-button link type="primary" @click="openVersion(item)"><el-icon><EditPen /></el-icon>基于此版本维护</el-button></article></div></section>
    <el-dialog v-model="dialogVisible" :title="editingTemplateId ? '维护标准模板新版本' : '新建脐橙周年管理模板'" width="min(1120px, calc(100% - 28px))" destroy-on-close><el-form label-position="top"><div class="form-grid"><el-form-item label="模板名称"><el-input v-model="form.name" :disabled="Boolean(editingTemplateId)"/></el-form-item><el-form-item label="品种"><el-input v-model="form.crop" :disabled="Boolean(editingTemplateId)"/></el-form-item><el-form-item label="适用地区"><el-input v-model="form.city" :disabled="Boolean(editingTemplateId)"/></el-form-item></div><el-form-item v-if="editingTemplateId" label="版本调整说明"><el-input v-model="form.changeNote" maxlength="500" show-word-limit placeholder="说明本版本调整的阶段、任务或频次"/></el-form-item><p class="form-note">生产年度固定为上年 12 月至当年 11 月。可维护阶段、任务、执行频次和土壤湿度目标；已发布版本不会被覆盖。</p><section v-for="(stage, stageIndex) in form.stages" :key="stageIndex" class="stage-editor"><header><strong>第 {{ stageIndex + 1 }} 阶段</strong><div class="stage-actions"><el-button link type="primary" @click="addTask(stage)"><el-icon><Plus/></el-icon>添加任务</el-button><el-button link type="danger" :disabled="form.stages.length === 1" @click="removeStage(stageIndex)"><el-icon><Delete/></el-icon>删除阶段</el-button></div></header><div class="stage-fields"><el-form-item label="阶段编号"><el-input v-model="stage.code"/></el-form-item><el-form-item label="阶段名称"><el-input v-model="stage.name"/></el-form-item><el-form-item label="阶段天数"><el-input-number v-model="stage.durationDays" :min="1" :max="366" controls-position="right"/></el-form-item><el-form-item label="土壤湿度下限（%）"><el-input-number v-model="stage.moistureMin" :min="0" :max="100" controls-position="right"/></el-form-item><el-form-item label="土壤湿度上限（%）"><el-input-number v-model="stage.moistureMax" :min="0" :max="100" controls-position="right"/></el-form-item><el-form-item label="管理重点"><el-input v-model="stage.managementFocus"/></el-form-item></div><div v-if="stage.tasks.length" class="task-columns"><span>适用轨道</span><span>农事任务</span><span>阶段第几天</span><span>执行频次</span><span>执行说明</span></div><div v-for="(entry, index) in stage.tasks" :key="index" class="task-row"><el-select v-model="entry.track"><el-option label="通用任务" :value="null"/><el-option label="幼树轨道" value="young"/><el-option label="结果树轨道" value="fruiting"/></el-select><el-input v-model="entry.title" placeholder="任务名称"/><el-input-number v-model="entry.offsetDays" :min="0" :max="Math.max(0, stage.durationDays - 1)" controls-position="right"/><el-select v-model="entry.repeatDays" placeholder="执行频次"><el-option label="仅执行一次" :value="null"/><el-option label="每 7 天" :value="7"/><el-option label="每 14 天" :value="14"/><el-option label="每 30 天" :value="30"/></el-select><el-input v-model="entry.note" placeholder="现场判断或执行说明"/><el-button circle text type="danger" title="删除任务" @click="removeTask(stage, index)"><el-icon><Delete/></el-icon></el-button></div><small v-if="!stage.tasks.length" class="empty-hint">本阶段暂无任务</small></section><el-button class="add-stage" plain type="primary" @click="addStage"><el-icon><Plus/></el-icon>添加生长阶段</el-button></el-form><template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="submit">{{ editingTemplateId ? '发布新版本' : '发布模板' }}</el-button></template></el-dialog>
  </div>
</template>

<style scoped>.template-library{padding:18px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:18px;color:#77728a;font-size:12px}.toolbar .el-input{width:310px}.template-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}.template-card{display:grid;align-content:start;gap:8px;min-height:165px;padding:17px;border:1px solid #e1dff0;border-radius:8px;background:#fff}.template-card span{color:#6b5bb5;font-size:12px;font-weight:700}.template-card h2,.template-card p{margin:0}.template-card h2{color:#302b45;font-size:16px}.template-card p,.template-card small{color:#817c91;font-size:12px}.template-card .el-button{justify-self:start;margin-top:4px}.form-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:12px}.form-note{margin:0 0 14px;color:#68776f;font-size:12px;line-height:1.6}.stage-editor{margin-bottom:11px;padding:13px;border:1px solid #e3e7e3;border-radius:8px;background:#fbfdfc}.stage-editor header{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:10px;color:#355447;font-size:13px}.stage-actions{display:flex;gap:6px}.stage-fields{display:grid;grid-template-columns:100px minmax(150px,1fr) 110px 150px 150px minmax(200px,1.3fr);gap:8px}.stage-fields :deep(.el-form-item){margin-bottom:10px}.stage-fields :deep(.el-input-number){width:100%}.empty-hint{color:#84938d;font-size:11px}.task-columns,.task-row{display:grid;grid-template-columns:128px minmax(150px,1fr) 105px 120px minmax(210px,1.35fr) 32px;gap:8px}.task-columns{padding:0 2px;color:#829089;font-size:11px}.task-row{margin-top:8px}.empty-hint{display:block;padding-top:8px}.add-stage{width:100%}@media(max-width:980px){.stage-fields{grid-template-columns:1fr 1fr 1fr}.task-row{grid-template-columns:1fr 1fr}.task-columns{display:none}}@media(max-width:820px){.toolbar{align-items:stretch;flex-direction:column}.toolbar .el-input{width:100%}.form-grid,.stage-fields,.task-row{grid-template-columns:1fr}.task-row .el-button{justify-self:end}.stage-editor header{align-items:flex-start;flex-direction:column}}</style>
