<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getFarmAnnualProduction, listFarms, saveFarmAnnualProduction } from '@/api/production'

const farms = ref([])
const selectedFarmId = ref('')
const current = ref(null)
const next = ref(null)
const loading = ref(false)
const saving = ref(false)
const form = reactive({ extendYoungTrack: false, trackOverrideReason: '' })
const nextYear = computed(() => (current.value?.productionYear || new Date().getFullYear()) + 1)
const autoTrack = computed(() => next.value?.treeAgeYears <= 3 ? 'young' : 'fruiting')
const canExtendYoung = computed(() => next.value?.treeAgeYears === 4 && autoTrack.value === 'fruiting')
const trackLabel = (track) => track === 'young' ? '幼树轨道' : '结果树轨道'

async function loadPlans() {
  current.value = null; next.value = null
  if (!selectedFarmId.value) return
  try {
    current.value = await getFarmAnnualProduction(selectedFarmId.value)
    next.value = await getFarmAnnualProduction(selectedFarmId.value, { productionYear: current.value.productionYear + 1 })
    form.extendYoungTrack = next.value.trackSource === 'extended_young'
    form.trackOverrideReason = next.value.trackOverrideReason || ''
  } catch (error) { ElMessage.error(error.message || '下一生产年度资料加载失败') }
}
async function loadResources() {
  loading.value = true
  try { farms.value = await listFarms(); selectedFarmId.value = farms.value[0]?.id || ''; await loadPlans() }
  catch (error) { ElMessage.error(error.message || '农场资料加载失败') }
  finally { loading.value = false }
}
function resetExtension(value) { if (!value) form.trackOverrideReason = '' }
async function save() {
  if (form.extendYoungTrack && !form.trackOverrideReason.trim()) return ElMessage.warning('请说明继续采用幼树轨道的原因')
  saving.value = true
  try {
    next.value = await saveFarmAnnualProduction(selectedFarmId.value, { productionYear: nextYear.value, templateVersionId: current.value.templateVersionId, extendYoungTrack: form.extendYoungTrack, trackOverrideReason: form.extendYoungTrack ? form.trackOverrideReason.trim() : null })
    ElMessage.success(`${nextYear.value} 生产年度方案已保存`)
  } catch (error) { ElMessage.error(error.message || '保存失败') }
  finally { saving.value = false }
}
onMounted(loadResources)
</script>

<template>
  <div class="farmer-page annual-draft-page">
    <div class="page-head"><div><h1 class="page-title">下一生产年度方案</h1><p class="page-subtitle">为全园确定下一年度统一轨道；公司标准模板不在这里逐项改写。</p></div></div>
    <el-skeleton v-if="loading" :rows="8" animated />
    <template v-else>
      <section class="farm-switcher"><span>当前农场</span><el-select v-model="selectedFarmId" size="large" @change="loadPlans"><el-option v-for="farm in farms" :key="farm.id" :label="`${farm.name} · ${farm.city || ''}`" :value="farm.id" /></el-select></section>
      <el-alert v-if="!current || !next" title="尚不能拟定下一生产年度方案" description="需要果园档案中的实际定植日期，以及已发布的生产模板。" type="warning" :closable="false" show-icon />
      <template v-else>
        <section class="content-panel year-bridge"><div><span>当前年度</span><strong>{{ current.productionYear }}</strong><small>{{ trackLabel(current.track) }}</small></div><el-icon><Right /></el-icon><div><span>下一年度</span><strong>{{ nextYear }}</strong><small>系统按树龄推荐 {{ trackLabel(autoTrack) }}</small></div></section>
        <section class="draft-layout">
          <article class="content-panel recommendation"><div class="section-head"><div><h3>系统推荐</h3><p>定植日期 {{ next.plantingDate }}，下一生产年度树龄为 {{ next.treeAgeYears }} 年。</p></div></div><div class="track-callout"><span>{{ autoTrack === 'young' ? '养树扩冠' : '产量与品质' }}</span><strong>{{ trackLabel(autoTrack) }}</strong><p>{{ autoTrack === 'young' ? '优先培养树形、促进枝梢生长，不下发保花保果和采收类建议。' : '围绕保花保果、稳果、壮果和适时采收安排建议。' }}</p></div></article>
          <article class="content-panel decision"><div class="section-head"><div><h3>年度轨道确认</h3><p>保存后作为全园下一生产年度的建议依据。</p></div></div><template v-if="canExtendYoung"><el-alert title="本园进入第 4 年，可申请延续幼树轨道一年" description="仅在树势偏弱等确有必要时使用，并留下原因供后续追溯。" type="warning" :closable="false" show-icon/><el-form label-position="top" class="extension-form"><el-form-item label="继续采用幼树轨道一年"><el-switch v-model="form.extendYoungTrack" active-text="继续幼树轨道" inactive-text="按系统推荐" @change="resetExtension" /></el-form-item><el-form-item v-if="form.extendYoungTrack" label="延期原因" required><el-input v-model="form.trackOverrideReason" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="例如：树势偏弱，尚未达到稳定结果条件" /></el-form-item></el-form></template><p v-else class="decision-note">{{ autoTrack === 'young' ? '树龄未满 4 年，系统将采用幼树轨道。' : '幼树轨道仅允许在进入第 4 年时延续一次；本年度将采用结果树轨道。' }}</p><el-button type="primary" :loading="saving" @click="save">保存下一年度方案</el-button></article>
        </section>
      </template>
    </template>
  </div>
</template>

<style scoped>
.farm-switcher{display:flex;align-items:center;gap:12px;margin-bottom:18px;padding:13px 16px;border:1px solid #cee6d8;border-radius:8px;background:#f8fcf9;color:#557164}.farm-switcher>span{color:#1f7a5b;font-size:12px;font-weight:700}.farm-switcher .el-select{width:300px}.year-bridge{display:flex;align-items:center;justify-content:center;gap:28px;margin-bottom:18px}.year-bridge>div{display:grid;gap:5px;min-width:150px}.year-bridge span,.year-bridge small{color:#84938d;font-size:11px}.year-bridge strong{color:#315447;font-size:25px}.year-bridge .el-icon{color:#e58226;font-size:23px}.draft-layout{display:grid;grid-template-columns:1fr 1fr;gap:18px}.track-callout{padding:20px;border-left:4px solid #e58226;background:#fff9f0}.track-callout span{color:#ad681f;font-size:12px}.track-callout strong{display:block;margin-top:7px;color:#315447;font-size:21px}.track-callout p,.decision-note{margin:10px 0 0;color:#657970;font-size:13px;line-height:1.7}.extension-form{margin-top:17px}.decision :deep(.el-alert){margin-bottom:17px}@media(max-width:700px){.farm-switcher{align-items:stretch;flex-direction:column}.farm-switcher .el-select{width:100%}.draft-layout{grid-template-columns:1fr}.year-bridge{justify-content:space-between;gap:10px}.year-bridge>div{min-width:0}}
</style>
