<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createCropTemplate, listCropTemplates } from '@/api/production'

const templates = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
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
function task(type, title, note, track = null) { return { type, title, offsetDays: 7, suggestedTime: null, note, track } }
const defaultTaskSets = {
  S1: [task('pruning', '冬季修剪与清园', '结合树势修剪，清除病虫枝和落叶。'), task('fertilization', '安排冬肥', '用量为参考值，结合土壤和树势调整。')],
  S2: [task('inspection', '巡园检查春梢长势', '记录新梢长度和病虫害情况。'), task('flower_management', '疏除花蕾', '幼树不留花果，减少养分消耗。', 'young'), task('fertilization', '催芽肥检查', '根据树势和土壤条件安排。', 'fruiting')],
  S3: [task('flower_management', '摘除小果', '幼树不留果，保持营养生长。', 'young'), task('flower_management', '保花保果巡查', '结合花量、树势和天气决定措施。', 'fruiting')],
  S4: [task('pruning', '夏梢管理', '幼树短截抹梢；结果树重点控夏梢。'), task('fruit_management', '第一次疏果', '仅结果树执行，去除小果、病虫果和畸形果。', 'fruiting')],
  S5: [task('irrigation', '检查土壤湿度与灌溉', '高温伏旱期及时灌溉或覆盖，结合天气调整。'), task('fruit_management', '第二次疏果', '按叶果比和树势调整负载。', 'fruiting')],
  S6: [task('pruning', '抹除晚秋梢', '关注 9 月中旬后抽生的新梢。'), task('inspection', '转色与病虫害巡查', '结果树关注果实转色和病虫害。', 'fruiting')],
  S7: [task('harvest', '成熟度检查', '果实完全转黄、糖酸比适宜时安排采收。', 'fruiting'), task('pruning', '采后修剪与清园准备', '幼树整形，结果树清除枯弱枝。')],
}
function defaultStages() {
  return stages.map(([code, name, period, durationDays, moistureMin, moistureMax, managementFocus]) => ({ code, name, period, durationDays, moistureMin, moistureMax, managementFocus, tasks: (defaultTaskSets[code] || []).map((item) => ({ ...item })) }))
}
const form = reactive({ name: '奉节脐橙全生命周期周年管理总模板', crop: '脐橙', province: '重庆市', city: '奉节县', stages: defaultStages() })
const filteredTemplates = computed(() => templates.value.filter((item) => `${item.name}${item.crop}${item.province || ''}${item.city || ''}`.toLowerCase().includes(keyword.value.toLowerCase())))
function resetForm() { Object.assign(form, { name: '奉节脐橙全生命周期周年管理总模板', crop: '脐橙', province: '重庆市', city: '奉节县', stages: defaultStages() }) }
function openCreate() { resetForm(); dialogVisible.value = true }
function addTask(stage) { stage.tasks.push(task('inspection', '巡园检查', '结合树势、土壤湿度和天气安排。')) }
function removeTask(stage, index) { stage.tasks.splice(index, 1) }
async function loadTemplates() { loading.value = true; try { templates.value = await listCropTemplates() } catch (error) { ElMessage.error(error.message || '模板列表加载失败') } finally { loading.value = false } }
function normalizedDefinition() {
  return { stages: form.stages.map((stage) => ({ code: stage.code, name: stage.name, durationDays: stage.durationDays, moistureMin: stage.moistureMin, moistureMax: stage.moistureMax, managementFocus: stage.managementFocus, tasks: stage.tasks.map((entry) => {
    if (!entry.type.trim() || !entry.title.trim()) throw new Error(`${stage.name} 中存在未填写完整的建议`)
    return { type: entry.type.trim(), title: entry.title.trim(), offsetDays: Number(entry.offsetDays || 7), suggestedTime: null, note: entry.note?.trim() || null, track: entry.track || null }
  }) })) }
}
async function submit() { saving.value = true; try { await createCropTemplate({ name: form.name.trim(), crop: form.crop.trim(), province: form.province.trim() || null, city: form.city.trim() || null, versionDefinition: normalizedDefinition() }); ElMessage.success('周年管理模板已发布'); dialogVisible.value = false; await loadTemplates() } catch (error) { ElMessage.error(error.message || '模板发布失败') } finally { saving.value = false } }
onMounted(loadTemplates)
</script>

<template>
  <div class="farmer-page templates-page">
    <div class="page-head"><div><h1 class="page-title">脐橙周年管理模板</h1><p class="page-subtitle">按固定物候期维护建议；具体执行由天气、土壤湿度和田间生长信号共同决定。</p></div><el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon>新建周年模板</el-button></div>
    <section class="content-panel template-library"><div class="toolbar"><el-input v-model="keyword" clearable placeholder="搜索模板、品种或地区"><template #prefix><el-icon><Search /></el-icon></template></el-input><span>已发布 {{ filteredTemplates.length }} 个</span></div><el-skeleton v-if="loading" :rows="5" animated/><el-empty v-else-if="!filteredTemplates.length" :image-size="74" description="暂无已发布的标准模板"/><div v-else class="template-grid"><article v-for="item in filteredTemplates" :key="item.versionId" class="template-card"><span>脐橙 · V{{ item.versionNo }}</span><h2>{{ item.name }}</h2><p>{{ item.province || '通用地区' }} {{ item.city || '' }}</p><small>7 个年度物候期 · 幼树/结果树双轨建议</small></article></div></section>
    <el-dialog v-model="dialogVisible" title="新建脐橙周年管理模板" width="min(980px, calc(100% - 28px))" destroy-on-close><el-form label-position="top"><div class="form-grid"><el-form-item label="模板名称"><el-input v-model="form.name"/></el-form-item><el-form-item label="品种"><el-input v-model="form.crop"/></el-form-item><el-form-item label="适用地区"><el-input v-model="form.city"/></el-form-item></div><p class="form-note">年度物候期固定为上年 12 月至当年 11 月。建议中的“阶段内参考日”仅用于生成初始待办，现场可调整。</p><section v-for="stage in form.stages" :key="stage.code" class="stage-editor"><header><div><strong>{{ stage.code }} · {{ stage.name }}</strong><small>{{ stage.period }} · 土壤湿度建议 {{ stage.moistureMin }}% - {{ stage.moistureMax }}%</small></div><el-button link type="primary" @click="addTask(stage)"><el-icon><Plus/></el-icon>添加建议</el-button></header><p>{{ stage.managementFocus }}</p><div v-for="(entry, index) in stage.tasks" :key="index" class="task-row"><el-select v-model="entry.track"><el-option label="通用建议" :value="null"/><el-option label="幼树轨道" value="young"/><el-option label="结果树轨道" value="fruiting"/></el-select><el-input v-model="entry.title" placeholder="建议事项"/><el-input v-model="entry.note" placeholder="现场判断或执行说明"/><el-button circle text type="danger" title="删除建议" @click="removeTask(stage, index)"><el-icon><Delete/></el-icon></el-button></div><small v-if="!stage.tasks.length" class="empty-hint">暂无建议</small></section></el-form><template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="submit">发布模板</el-button></template></el-dialog>
  </div>
</template>

<style scoped>.template-library{padding:18px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:18px;color:#77728a;font-size:12px}.toolbar .el-input{width:310px}.template-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}.template-card{display:grid;gap:8px;min-height:135px;padding:17px;border:1px solid #e1dff0;border-radius:8px;background:#fff}.template-card span{color:#6b5bb5;font-size:12px;font-weight:700}.template-card h2,.template-card p{margin:0}.template-card h2{color:#302b45;font-size:16px}.template-card p,.template-card small{color:#817c91;font-size:12px}.form-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:12px}.form-note{margin:0 0 14px;color:#68776f;font-size:12px;line-height:1.6}.stage-editor{margin-bottom:11px;padding:13px;border:1px solid #e3e7e3;border-radius:8px;background:#fbfdfc}.stage-editor header{display:flex;justify-content:space-between;align-items:center;gap:12px}.stage-editor header div{display:grid;gap:4px;color:#355447;font-size:13px}.stage-editor header small,.empty-hint{color:#84938d;font-size:11px}.stage-editor p{margin:9px 0;color:#63776e;font-size:12px}.task-row{display:grid;grid-template-columns:130px 1fr 1.4fr 32px;gap:8px;margin-top:8px}.empty-hint{display:block;padding-top:3px}@media(max-width:700px){.toolbar{align-items:stretch;flex-direction:column}.toolbar .el-input{width:100%}.form-grid,.task-row{grid-template-columns:1fr}.task-row .el-button{position:absolute;right:36px}.stage-editor header{align-items:flex-start;flex-direction:column}}</style>
